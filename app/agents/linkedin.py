"""LinkedIn agent executor."""

from __future__ import annotations

from collections.abc import Iterator

from openai import OpenAI

from app.agents.agent_types import AgentRequest, AgentResponse
from config import Config

SYSTEM_PROMPT = (
    "You are a professional linkedin copywriter to create high engagement "
    "linkedin posts"
)


def _build_prompt(request: AgentRequest) -> str:
    return (
        f"Original User Request: {request.original_query}\n"
        f"Refined Query: {request.query}"
    )


def stream_linkedin_agent(request: AgentRequest) -> Iterator[str]:
    """Yield LinkedIn response chunks as they arrive from OpenAI."""

    model = Config.OPENAI_FINETUNED_MODEL
    if not model:
        raise ValueError(
            "OPENAI_FINETUNED_MODEL is not configured. "
            "Set it in .env (e.g. ft:gpt-4o-mini-2024-07-18:org:model:id)."
        )

    prompt = _build_prompt(request)

    client = OpenAI(api_key=Config.OPENAI_API_KEY)
    stream = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.8,
        stream=True,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        if delta:
            yield delta


def linkedin_agent(request: AgentRequest) -> AgentResponse:
    """Generate a LinkedIn post from user intent and selector-refined query.
    NOTE:
      - better to stream text; did not find Python option for this feature
      - for example, TypeScript's Vercel AI SDK
      - defaulting to OpenAI Python SDK chat completions API
      - return generated text as the normalized 'AgentResponse'
    """

    model = Config.OPENAI_FINETUNED_MODEL
    if not model:
        raise ValueError(
            "OPENAI_FINETUNED_MODEL is not configured. "
            "Set it in .env (e.g. ft:gpt-4o-mini-2024-07-18:org:model:id)."
        )

    client = OpenAI(api_key=Config.OPENAI_API_KEY)
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_prompt(request)},
        ],
        temperature=0.8,
    )

    return AgentResponse(
        agent="linkedin",
        content=completion.choices[0].message.content or "",
    )
