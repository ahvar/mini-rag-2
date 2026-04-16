"""Agent registry and built-in agent executors."""

from __future__ import annotations

from typing import Callable, Dict, cast

from langchain_openai import OpenAIEmbeddings
from openai import OpenAI

from app.agents.agent_types import AgentRequest, AgentResponse, AgentType
from app.agents.linkedin import linkedin_agent
from app.main.pinecone_client import PineconeClient
from config import Config

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 512

AgentExecutor = Callable[[AgentRequest], AgentResponse]


def _messages_to_openai(messages: list[dict]) -> list[dict[str, str]]:
    return [
        {"role": message.get("role", "user"), "content": message.get("content", "")}
        for message in messages
    ]


def rag_agent(request: AgentRequest) -> AgentResponse:
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
    # Initial overfetch for reranking
    query_response = pinecone_client.query_vectors(
        vector=query_embedding,
        top_k=Config.RAG_INITIAL_FETCH,
        include_metadata=True,
    )
    matches = getattr(query_response, "matches", None)
    if matches is None and isinstance(query_response, dict):
        matches = query_response.get("matches", [])

    # Extract documents for reranking
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

    # Rerank using Pinecone's inference API
    reranked = pinecone_client.rerank(
        model="bge-reranker-v2-m3",
        query=request.query,
        documents=documents,
        top_n=Config.RAG_TOP_K,
        return_documents=True,
    )

    # Build contexts from reranked results
    contexts: list[dict] = []
    snippets = []
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

    client = OpenAI(api_key=Config.OPENAI_API_KEY)
    completion = client.chat.completions.create(
        model=Config.BASE_MODEL,
        messages=[
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
        ],
        temperature=0.2,
    )

    content = completion.choices[0].message.content or ""
    return AgentResponse(agent="rag", content=content, context=contexts)


agent_registry: Dict[AgentType, AgentExecutor] = {
    "linkedin": linkedin_agent,
    "rag": rag_agent,
}


def get_agent(agent_type: AgentType) -> AgentExecutor:
    agent = agent_registry.get(agent_type)
    if agent is None:
        raise ValueError(f"Unknown agent type: {agent_type}")
    return cast(AgentExecutor, agent)
