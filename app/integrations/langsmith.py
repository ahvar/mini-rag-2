from __future__ import annotations

from typing import Any

from langsmith import traceable

from app.agents.agent_types import AgentRequest, AgentResponse, StreamingAgentResponse


def serialize_selector_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    messages = inputs.get("messages")
    if not isinstance(messages, list):
        return {"message_count": 0, "messages": []}

    recent_messages = []
    for message in messages[-5:]:
        if not isinstance(message, dict):
            continue
        role = message.get("role")
        content = message.get("content")
        if isinstance(role, str) and isinstance(content, str):
            recent_messages.append({"role": role, "content": content})

    return {
        "message_count": len(messages),
        "messages": recent_messages,
    }


def serialize_agent_request_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    request = inputs.get("request")
    if not isinstance(request, AgentRequest):
        return inputs

    return {
        "request": {
            "type": request.type,
            "query": request.query,
            "original_query": request.original_query,
            "message_count": len(request.messages),
        }
    }


def serialize_agent_response(output: Any) -> dict[str, Any]:
    if not isinstance(output, AgentResponse):
        return {"output_type": type(output).__name__}

    return {
        "agent": output.agent,
        "content": output.content,
        "context_count": len(output.context or []),
        "sources_count": len(output.sources or []),
    }


def serialize_streaming_agent_response(output: Any) -> dict[str, Any]:
    if not isinstance(output, StreamingAgentResponse):
        return {"output_type": type(output).__name__}

    return {
        "sources_count": len(output.sources or []),
    }


def serialize_rag_context_output(output: Any) -> dict[str, Any]:
    if not isinstance(output, tuple) or len(output) != 3:
        return {"output_type": type(output).__name__}

    contexts, snippets, sources = output
    return {
        "context_count": len(contexts) if isinstance(contexts, list) else None,
        "snippet_count": len(snippets) if isinstance(snippets, list) else None,
        "sources_count": len(sources) if isinstance(sources, list) else None,
    }
