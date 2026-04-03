"""Agent configuration definitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class AgentConfig:
    name: str
    description: str


AgentType = str


agent_configs: Dict[AgentType, AgentConfig] = {
    "linkedin": AgentConfig(
        name="LinkedIn Agent",
        description="For writing posts in a certain voice and tone for LinkedIn",
    ),
    "rag": AgentConfig(
        name="RAG Agent",
        description=(
            "For questions about documentation regarding Typescript, NextJS, "
            "Pinecone, Vercel AI SDK technical content, or information that "
            "requires knowledge base retrieval"
        ),
    ),
}
