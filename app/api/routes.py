from __future__ import annotations

import json

from flask import jsonify, request
from langchain_openai import OpenAIEmbeddings
from openai import OpenAI

from app.agents.agent_config import agent_configs
from app.agents.registry import get_agent
from app.agents.types import AgentRequest, AgentType, Message
from app.api import bp
from app.main.pinecone_client import PineconeClient
from config import Config

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 512


@bp.route("/api/test-rag/<query>", methods=["PUT"])
def test_rag(query: str):
    embeddings_client = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        dimensions=EMBEDDING_DIMENSIONS,
        api_key=Config.OPENAI_API_KEY,
    )
    query_embedding = embeddings_client.embed_query(query)

    pinecone_client = PineconeClient(
        api_key=Config.PINECONE_API_KEY,
        index_name=Config.PINECONE_INDEX,
        namespace=Config.PINECONE_NAMESPACE,
    )

    query_response = pinecone_client.query_vectors(
        vector=query_embedding,
        top_k=Config.RAG_TOP_K,
        include_metadata=True,
    )
    matches = getattr(query_response, "matches", None)
    if matches is None and isinstance(query_response, dict):
        matches = query_response.get("matches", [])

    result = [
        {
            "id": match.get("id") if isinstance(match, dict) else getattr(match, "id", None),
            "score": match.get("score") if isinstance(match, dict) else getattr(match, "score", None),
            "metadata": match.get("metadata") if isinstance(match, dict) else getattr(match, "metadata", {}),
        }
        for match in (matches or [])
    ]
    return jsonify(result)


def select_agent(messages: list[Message]) -> tuple[AgentType, str]:
    recent_messages = messages[-5:]
    agent_descriptions = "\n".join(
        f'- "{key}": {config.description}' for key, config in agent_configs.items()
    )

    selector_prompt = (
        "You are a selector agent. Analyze the recent conversation, identify user intent, remove "
        "conversational noise, and return JSON with keys 'agent' and 'query'. "
        "Choose only one agent from: linkedin or rag."
    )

    client = OpenAI(api_key=Config.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=Config.OPENAI_FINETUNED_MODEL or Config.BASE_MODEL,
        response_format={"type": "json_object"},
        temperature=0,
        messages=[
            {"role": "system", "content": selector_prompt},
            {
                "role": "system",
                "content": f"Available agents:\n{agent_descriptions}",
            },
            {
                "role": "user",
                "content": "Conversation:\n"
                + "\n".join(f"{m['role']}: {m['content']}" for m in recent_messages),
            },
        ],
    )

    raw_content = response.choices[0].message.content or "{}"
    parsed = json.loads(raw_content)
    agent = parsed.get("agent", "rag")
    query = parsed.get("query") or (messages[-1]["content"] if messages else "")

    if agent not in {"linkedin", "rag"}:
        agent = "rag"

    return agent, query


@bp.route("/api/select-agent", methods=["POST"])
def select_agent_route():
    try:
        body = request.get_json(silent=True) or {}
        messages = body.get("messages", [])
        if not isinstance(messages, list) or len(messages) == 0:
            return jsonify({"error": "messages must be a non-empty list"}), 400

        normalized_messages: list[Message] = []
        for message in messages:
            if not isinstance(message, dict):
                continue
            role = message.get("role")
            content = message.get("content")
            if role in {"user", "assistant", "system"} and isinstance(content, str):
                normalized_messages.append({"role": role, "content": content})

        if not normalized_messages:
            return jsonify({"error": "no valid messages supplied"}), 400

        agent, query = select_agent(normalized_messages)
        return jsonify({"agent": agent, "query": query})
    except Exception as exc:
        return jsonify({"error": f"Failed to select agent: {exc}"}), 500


@bp.route("/api/chat", methods=["POST"])
def chat_route():
    try:
        body = request.get_json(silent=True) or {}
        messages = body.get("messages", [])
        agent = body.get("agent")
        query = body.get("query", "")

        if agent not in {"linkedin", "rag"}:
            return jsonify({"error": "agent must be one of linkedin or rag"}), 400

        normalized_messages: list[Message] = []
        for message in messages:
            if not isinstance(message, dict):
                continue
            role = message.get("role")
            content = message.get("content")
            if role in {"user", "assistant", "system"} and isinstance(content, str):
                normalized_messages.append({"role": role, "content": content})

        original_query = (
            normalized_messages[-1]["content"] if normalized_messages else str(query)
        )
        request_obj = AgentRequest(
            type=agent,
            query=str(query or original_query),
            original_query=original_query,
            messages=normalized_messages,
        )

        agent_executor = get_agent(agent)
        result = agent_executor(request_obj)
        return jsonify(
            {
                "agent": result.agent,
                "response": result.content,
                "context": result.context or [],
            }
        )
    except Exception as exc:
        return jsonify({"error": f"Failed to process chat: {exc}"}), 500
