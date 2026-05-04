from __future__ import annotations

from pydantic import BaseModel, Field

from app.integrations.openai import create_openai_client
from config import Config

JUDGE_SYSTEM_PROMPT = """You are an expert evaluator assessing AI response quality.

Compare the ACTUAL response against the REFERENCE response and score from 1-10:

SCORING CRITERIA:
- 10: Perfect - covers all key points, equally or more helpful
- 8-9: Excellent - covers most key points, minor omissions
- 6-7: Good - covers main idea but missing important details
- 4-5: Fair - partially correct but significant gaps
- 2-3: Poor - mostly incorrect or unhelpful
- 1: Failed - completely wrong or off-topic

IMPORTANT:
- Focus on factual accuracy and completeness
- The actual response doesn't need identical wording
- It CAN be better than the reference (still scores 10)
- Penalize incorrect information heavily"""


class JudgeResult(BaseModel):
    score: int = Field(ge=1, le=10)
    reason: str


class RawJudgeResult(BaseModel):
    score: int = Field(ge=1)
    reason: str


def judge_response(question: str, actual_response: str, golden_response: str) -> JudgeResult:
    """Use the LLM as a quality judge against a golden response."""

    client = create_openai_client()
    response = client.beta.chat.completions.parse(
        model=Config.BASE_MODEL,
        temperature=0,
        response_format=RawJudgeResult,
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"QUESTION: {question}\n\n"
                    f"REFERENCE RESPONSE:\n{golden_response}\n\n"
                    f"ACTUAL RESPONSE:\n{actual_response}\n\n"
                    "Score the actual response against the reference."
                ),
            },
        ],
    )

    parsed_result = response.choices[0].message.parsed
    if parsed_result is None:
        raise ValueError("Judge returned no structured output")

    return JudgeResult(score=min(parsed_result.score, 10), reason=parsed_result.reason)
