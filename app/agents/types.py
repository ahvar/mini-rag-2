"""Common agent request/response contracts and shared message typing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypedDict

AgentType = Literal["linkedin", "rag"]
MessageRole = Literal["user", "assistant", "system"]


class Message(TypedDict):
    role: MessageRole
    content: str


@dataclass(frozen=True)
class AgentRequest:
    """Contract consumed by every agent executor."""

    type: AgentType
    query: str
    original_query: str
    messages: list[Message]


@dataclass(frozen=True)
class AgentResponse:
    """Normalized agent execution result for HTTP responses."""

    agent: AgentType
    content: str
    context: list[dict] | None = None
