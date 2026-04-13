"""LinkedIn agent executor."""

from __future__ import annotations

from openai import OpenAI

from app.agents.agent_types import AgentRequest, AgentResponse
from config import Config


SYSTEM_PROMPT = (
    "You are a professional linkedin copywriter to create high engagement "
    "linkedin posts"
)


def linkedin_agent(request: AgentRequest) -> AgentResponse:
    """Generate a LinkedIn post from user intent and selector-refined query.

    TypeScript's Vercel AI SDK `streamText()` does not have a direct Python
    equivalent in this project stack. We use the OpenAI Python SDK chat
    completions API and return the generated text as the normalized
    ``AgentResponse``.
    """

    model = Config.OPENAI_FINETUNED_MODEL
    if not model:
        raise ValueError(
            "OPENAI_FINETUNED_MODEL is not configured. "
            "Set it in .env (e.g. ft:gpt-4o-mini-2024-07-18:org:model:id)."
        )

    prompt = (
        f"Original User Request: {request.original_query}\n"
        f"Refined Query: {request.query}"
    )

    client = OpenAI(api_key=Config.OPENAI_API_KEY)
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.8,
    )

    return AgentResponse(
        agent="linkedin",
        content=completion.choices[0].message.content or "",
    )
