"""Agent registry and built-in agent executors."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any, Callable, Dict, cast
from urllib.parse import urlparse

from langchain_openai import OpenAIEmbeddings

from app.agents.agent_types import (
    AgentRequest,
    AgentResponse,
    AgentType,
    RagContextItem,
    SourceReference,
    StreamingAgentResponse,
)
from app.agents.linkedin import linkedin_agent, stream_linkedin_agent
from app.integrations.langsmith import (
    serialize_agent_request_inputs,
    serialize_agent_response,
    serialize_rag_context_output,
    serialize_streaming_agent_response,
    traceable,
)
from app.integrations.openai import create_openai_client
from app.main.pinecone_client import PineconeClient
from config import Config

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 512

AgentExecutor = Callable[[AgentRequest], AgentResponse]
StreamingAgentExecutor = Callable[[AgentRequest], StreamingAgentResponse]


def _messages_to_openai(messages: list[dict]) -> list[dict[str, str]]:
    return [
        {"role": message.get("role", "user"), "content": message.get("content", "")}
        for message in messages
    ]


def _extract_match_metadata(match: Any) -> dict[str, Any]:
    metadata = (
        match.get("metadata")
        if isinstance(match, dict)
        else getattr(match, "metadata", {})
    )
    return metadata if isinstance(metadata, dict) else {}


def _extract_match_text(metadata: dict[str, Any]) -> str:
    text = metadata.get("text") or metadata.get("chunk")
    return text.strip() if isinstance(text, str) else ""


def _normalize_source_url(metadata: dict[str, Any]) -> str | None:
    raw_url = metadata.get("url") or metadata.get("source")
    if not isinstance(raw_url, str):
        return None

    url = raw_url.strip()
    if not url:
        return None

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None

    return url


def _build_source_title(metadata: dict[str, Any], url: str | None) -> str:
    raw_title = metadata.get("title")
    if isinstance(raw_title, str) and raw_title.strip():
        return raw_title.strip()

    raw_source = metadata.get("source")
    if isinstance(raw_source, str) and raw_source.strip():
        return raw_source.strip()

    if url:
        hostname = urlparse(url).netloc
        if hostname:
            return hostname

    return "Untitled"


def _build_source_reference(
    metadata: dict[str, Any], score: float | None
) -> SourceReference | None:
    url = _normalize_source_url(metadata)
    if url is None:
        return None

    return {
        "title": _build_source_title(metadata, url),
        "url": url,
        "score": score,
    }


def _iter_openai_chunks(stream: Iterator[Any]) -> Iterator[str]:
    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        if delta:
            yield delta


@traceable(
    name="build_rag_context",
    run_type="retriever",
    process_inputs=serialize_agent_request_inputs,
    process_outputs=serialize_rag_context_output,
)
def _build_rag_context(
    request: AgentRequest,
) -> tuple[list[RagContextItem], list[str], list[SourceReference]]:
    embeddings_client = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        dimensions=EMBEDDING_DIMENSIONS,
        api_key=Config.OPENAI_API_KEY,
    )
    query_embedding = embeddings_client.embed_query(request.query)

    pinecone_client = PineconeClient(
        api_key=Config.PINECONE_API_KEY,
        index_name=Config.PINECONE_INDEX,
        namespace=Config.PINECONE_NAMESPACE,
    )
    query_response = pinecone_client.query_vectors(
        vector=query_embedding,
        top_k=Config.RAG_INITIAL_FETCH,
        include_metadata=True,
    )
    matches = getattr(query_response, "matches", None)
    if matches is None and isinstance(query_response, dict):
        matches = query_response.get("matches", [])

    documents: list[dict[str, Any]] = []
    for match in matches or []:
        metadata = _extract_match_metadata(match)
        text = _extract_match_text(metadata)
        if text:
            documents.append(
                {
                    "metadata": metadata,
                    "text": text,
                }
            )

    if not documents:
        return [], [], []

    reranked = pinecone_client.rerank(
        model="bge-reranker-v2-m3",
        query=request.query,
        documents=[document["text"] for document in documents],
        top_n=Config.RAG_TOP_K,
        return_documents=True,
    )

    contexts: list[RagContextItem] = []
    snippets: list[str] = []
    sources: list[SourceReference] = []
    seen_source_urls: set[str] = set()
    for result in reranked.get("data", []):
        index = result.get("index")
        if not isinstance(index, int) or index < 0 or index >= len(documents):
            continue

        document = documents[index]
        text = document["text"]
        score_value = result.get("score")
        score = float(score_value) if isinstance(score_value, (int, float)) else None
        if text:
            snippets.append(f"- {text}")
            contexts.append(
                {
                    "index": index,
                    "score": score,
                    "text": text,
                }
            )
            source = _build_source_reference(document["metadata"], score)
            if source is not None and source["url"] not in seen_source_urls:
                seen_source_urls.add(source["url"])
                sources.append(source)

    return contexts, snippets, sources


def _build_rag_messages(
    request: AgentRequest, snippets: list[str]
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are a technical support assistant. Use retrieved context when helpful and "
                "state uncertainty when context is insufficient."
            ),
        },
        *_messages_to_openai(request.messages),
        {
            "role": "user",
            "content": (
                f"User question: {request.query}\n\nRetrieved context:\n"
                + ("\n".join(snippets) if snippets else "No context retrieved.")
            ),
        },
    ]


@traceable(
    name="stream_rag_agent",
    run_type="chain",
    process_inputs=serialize_agent_request_inputs,
    process_outputs=serialize_streaming_agent_response,
)
def stream_rag_agent(request: AgentRequest) -> StreamingAgentResponse:
    """Yield RAG response chunks after retrieval and reranking."""

    _, snippets, sources = _build_rag_context(request)

    client = create_openai_client()
    stream = client.chat.completions.create(
        model=Config.BASE_MODEL,
        messages=_build_rag_messages(request, snippets),
        temperature=0.2,
        stream=True,
    )

    return StreamingAgentResponse(
        stream=_iter_openai_chunks(stream),
        sources=sources,
    )


@traceable(
    name="rag_agent",
    run_type="chain",
    process_inputs=serialize_agent_request_inputs,
    process_outputs=serialize_agent_response,
)
def rag_agent(request: AgentRequest) -> AgentResponse:
    contexts, snippets, sources = _build_rag_context(request)

    client = create_openai_client()
    completion = client.chat.completions.create(
        model=Config.BASE_MODEL,
        messages=_build_rag_messages(request, snippets),
        temperature=0.2,
    )

    return AgentResponse(
        agent="rag",
        content=completion.choices[0].message.content or "",
        context=contexts,
        sources=sources,
    )


agent_registry: Dict[AgentType, AgentExecutor] = {
    "linkedin": linkedin_agent,
    "rag": rag_agent,
}

streaming_agent_registry: Dict[AgentType, StreamingAgentExecutor] = {
    "linkedin": stream_linkedin_agent,
    "rag": stream_rag_agent,
}


def get_agent(agent_type: AgentType) -> AgentExecutor:
    agent = agent_registry.get(agent_type)
    if agent is None:
        raise ValueError(f"Unknown agent type: {agent_type}")
    return cast(AgentExecutor, agent)


def get_streaming_agent(agent_type: AgentType) -> StreamingAgentExecutor:
    agent = streaming_agent_registry.get(agent_type)
    if agent is None:
        raise ValueError(f"Unknown agent type: {agent_type}")
    return cast(StreamingAgentExecutor, agent)
