"""Common agent request/response contracts and shared message typing."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Literal, TypedDict

AgentType = Literal["linkedin", "rag"]
MessageRole = Literal["user", "assistant", "system"]


class Message(TypedDict):
    role: MessageRole
    content: str


class RagContextItem(TypedDict):
    index: int | None
    score: float | None
    text: str


class SourceReference(TypedDict):
    title: str
    url: str
    score: float | None


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
    context: list[RagContextItem] | None = None
    sources: list[SourceReference] | None = None


@dataclass(frozen=True)
class StreamingAgentResponse:
    """Normalized streaming result used by the HTTP layer."""

    stream: Iterator[str]
    sources: list[SourceReference] | None = None
