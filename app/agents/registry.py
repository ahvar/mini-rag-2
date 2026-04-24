"""Agent registry and built-in agent executors."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Callable, Dict, cast

from langchain_openai import OpenAIEmbeddings
from openai import OpenAI

from app.agents.agent_types import AgentRequest, AgentResponse, AgentType
from app.agents.linkedin import linkedin_agent, stream_linkedin_agent
from app.main.pinecone_client import PineconeClient
from config import Config

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 512

AgentExecutor = Callable[[AgentRequest], AgentResponse]
StreamingAgentExecutor = Callable[[AgentRequest], Iterator[str]]


def _messages_to_openai(messages: list[dict]) -> list[dict[str, str]]:
    return [
        {"role": message.get("role", "user"), "content": message.get("content", "")}
        for message in messages
    ]


def _build_rag_context(request: AgentRequest) -> tuple[list[dict], list[str]]:
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

    documents = []
    for match in matches or []:
        metadata = (
            match.get("metadata")
            if isinstance(match, dict)
            else getattr(match, "metadata", {})
        )
        text = metadata.get("text") or metadata.get("chunk") or str(metadata)
        if text:
            documents.append(text)

    reranked = pinecone_client.rerank(
        model="bge-reranker-v2-m3",
        query=request.query,
        documents=documents,
        top_n=Config.RAG_TOP_K,
        return_documents=True,
    )

    contexts: list[dict] = []
    snippets: list[str] = []
    for result in reranked.get("data", []):
        document = result.get("document", {})
        text = document.get("text", "")
        if text:
            snippets.append(f"- {text}")
            contexts.append(
                {
                    "index": result.get("index"),
                    "score": result.get("score"),
                    "text": text,
                }
            )

    return contexts, snippets


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


def stream_rag_agent(request: AgentRequest) -> Iterator[str]:
    """Yield RAG response chunks after retrieval and reranking."""

    _, snippets = _build_rag_context(request)

    client = OpenAI(api_key=Config.OPENAI_API_KEY)
    stream = client.chat.completions.create(
        model=Config.BASE_MODEL,
        messages=_build_rag_messages(request, snippets),
        temperature=0.2,
        stream=True,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        if delta:
            yield delta


def rag_agent(request: AgentRequest) -> AgentResponse:
    contexts, snippets = _build_rag_context(request)

    client = OpenAI(api_key=Config.OPENAI_API_KEY)
    completion = client.chat.completions.create(
        model=Config.BASE_MODEL,
        messages=_build_rag_messages(request, snippets),
        temperature=0.2,
    )

    return AgentResponse(
        agent="rag",
        content=completion.choices[0].message.content or "",
        context=contexts,
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
