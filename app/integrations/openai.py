from __future__ import annotations

from langsmith.wrappers import wrap_openai
from openai import OpenAI

from config import Config


def create_openai_client() -> OpenAI:
    return wrap_openai(OpenAI(api_key=Config.OPENAI_API_KEY))
