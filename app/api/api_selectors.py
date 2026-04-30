from __future__ import annotations

from collections.abc import Iterator
import json

from pydantic import BaseModel

from app.agents.agent_config import agent_configs
from app.agents.registry import get_agent, get_streaming_agent
from app.agents.agent_types import AgentRequest, AgentType, Message, SourceReference
from app.api import bp
from app.integrations.langsmith import serialize_selector_inputs, traceable
from app.integrations.openai import create_openai_client
from config import Config
from flask import Response, jsonify, request, stream_with_context

STREAMING_ERROR_MESSAGE = "\n\n[Streaming error]"
CHAT_SOURCES_HEADER = "X-Chat-Sources"


class AgentSelection(BaseModel):
    agent: AgentType
    query: str


@traceable(
    name="select_agent",
    run_type="tool",
    process_inputs=serialize_selector_inputs,
)
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

    client = create_openai_client()
    response = client.beta.chat.completions.parse(
        model=Config.BASE_MODEL,
        response_format=AgentSelection,
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

    parsed_selection = response.choices[0].message.parsed
    agent = parsed_selection.agent if parsed_selection is not None else "rag"
    query = (
        parsed_selection.query
        if parsed_selection is not None and parsed_selection.query
        else (messages[-1]["content"] if messages else "")
    )

    return agent, query


def normalize_messages(messages: list) -> list[Message]:
    """Validate and normalize message list from request body.

    Filters out invalid messages and ensures each message has:
    - role: one of 'user', 'assistant', or 'system'
    - content: a non-empty string
    """
    normalized: list[Message] = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        role = message.get("role")
        content = message.get("content")
        if role in {"user", "assistant", "system"} and isinstance(content, str):
            normalized.append({"role": role, "content": content})
    return normalized


def _get_request_body() -> dict:
    body = request.get_json(silent=True)
    if body is None:
        return {}
    if not isinstance(body, dict):
        raise ValueError("request body must be a JSON object")
    return body


def _build_agent_request(body: dict) -> AgentRequest:
    messages = body.get("messages", [])
    agent = body.get("agent")
    query = body.get("query", "")

    if agent not in {"linkedin", "rag"}:
        raise ValueError("agent must be one of linkedin or rag")

    normalized_messages = normalize_messages(messages)
    original_query = (
        normalized_messages[-1]["content"] if normalized_messages else str(query)
    )
    return AgentRequest(
        type=agent,
        query=str(query or original_query),
        original_query=original_query,
        messages=normalized_messages,
    )


def _stream_chat_chunks(stream: Iterator[str]) -> Iterator[str]:
    try:
        for chunk in stream:
            if chunk:
                yield chunk
    except Exception:
        yield STREAMING_ERROR_MESSAGE


def _serialize_sources(sources: list[SourceReference]) -> str:
    return json.dumps(sources, separators=(",", ":"))


@bp.route("/api/select-agent", methods=["POST"])
def select_agent_route():
    try:
        body = _get_request_body()
        messages = body.get("messages", [])
        if not isinstance(messages, list) or len(messages) == 0:
            return jsonify({"error": "messages must be a non-empty list"}), 400

        normalized_messages = normalize_messages(messages)
        if not normalized_messages:
            return jsonify({"error": "no valid messages supplied"}), 400

        agent, query = select_agent(normalized_messages)
        return jsonify({"agent": agent, "query": query})
    except Exception as exc:
        return jsonify({"error": f"Failed to select agent: {exc}"}), 500


@bp.route("/api/chat", methods=["POST"])
def chat_route():
    try:
        body = _get_request_body()
        request_obj = _build_agent_request(body)

        agent_executor = get_agent(request_obj.type)
        result = agent_executor(request_obj)
        payload = {
            "agent": result.agent,
            "response": result.content,
            "context": result.context or [],
        }
        if result.sources is not None:
            payload["sources"] = result.sources
        return jsonify(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        return jsonify({"error": "Failed to process chat"}), 500


@bp.route("/api/chat-stream", methods=["POST"])
def chat_stream_route():
    try:
        body = _get_request_body()
        request_obj = _build_agent_request(body)
        agent_executor = get_streaming_agent(request_obj.type)
        result = agent_executor(request_obj)

        response = Response(
            stream_with_context(_stream_chat_chunks(result.stream)),
            mimetype="text/plain",
        )
        if result.sources:
            response.headers[CHAT_SOURCES_HEADER] = _serialize_sources(result.sources)
        return response
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        return jsonify({"error": "Failed to process streaming chat"}), 500
