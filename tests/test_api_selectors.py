from __future__ import annotations

from types import SimpleNamespace
from unittest import mock

from app import create_app
import app.api.api_selectors as api_selectors
from app.api.api_selectors import select_agent
from test_config import TestConfig


class TestApiSelectors:
    def setup_method(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()

    def teardown_method(self):
        self.app_context.pop()

    def test_select_agent_uses_structured_output_parse_and_returns_parsed_values(self):
        messages = [
            {"role": "user", "content": "Can you summarize my LinkedIn profile?"},
        ]

        with (
            mock.patch("app.api.api_selectors.Config", TestConfig),
            mock.patch("app.api.api_selectors.OpenAI") as MockOpenAI,
        ):
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

            MockOpenAI.assert_called_once_with(api_key=TestConfig.OPENAI_API_KEY)
            client.beta.chat.completions.parse.assert_called_once()
            _, kwargs = client.beta.chat.completions.parse.call_args
            assert kwargs["response_format"] is api_selectors.AgentSelection
            assert kwargs["temperature"] == 0
            assert kwargs["model"] == TestConfig.BASE_MODEL

            assert agent == "linkedin"
            assert query == "summarize my LinkedIn profile"

    def test_select_agent_falls_back_when_no_parsed_output(self):
        messages = [{"role": "user", "content": "What is retrieval augmented generation?"}]

        with (
            mock.patch("app.api.api_selectors.Config", TestConfig),
            mock.patch("app.api.api_selectors.OpenAI") as MockOpenAI,
        ):
            client = MockOpenAI.return_value
            client.beta.chat.completions.parse.return_value = SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(parsed=None))]
            )

            agent, query = select_agent(messages)

            MockOpenAI.assert_called_once_with(api_key=TestConfig.OPENAI_API_KEY)
            assert agent == "rag"
            assert query == "What is retrieval augmented generation?"
