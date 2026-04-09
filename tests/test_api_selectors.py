from __future__ import annotations

from types import SimpleNamespace
from unittest import mock

from app.api.api_selectors import select_agent


def test_select_agent_uses_structured_output_parse_and_returns_parsed_values():
    messages = [
        {"role": "user", "content": "Can you summarize my LinkedIn profile?"},
    ]

    with mock.patch("app.api.api_selectors.OpenAI") as MockOpenAI:
        client = MockOpenAI.return_value
        client.beta.chat.completions.parse.return_value = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        parsed=SimpleNamespace(
                            agent="linkedin",
                            query="summarize my LinkedIn profile",
                        )
                    )
                )
            ]
        )

        agent, query = select_agent(messages)

        client.beta.chat.completions.parse.assert_called_once()
        _, kwargs = client.beta.chat.completions.parse.call_args
        assert kwargs["response_format"].__name__ == "AgentSelection"
        assert kwargs["temperature"] == 0
        assert kwargs["model"]

        assert agent == "linkedin"
        assert query == "summarize my LinkedIn profile"


def test_select_agent_falls_back_when_no_parsed_output():
    messages = [{"role": "user", "content": "What is retrieval augmented generation?"}]

    with mock.patch("app.api.api_selectors.OpenAI") as MockOpenAI:
        client = MockOpenAI.return_value
        client.beta.chat.completions.parse.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(parsed=None))]
        )

        agent, query = select_agent(messages)

        assert agent == "rag"
        assert query == "What is retrieval augmented generation?"
