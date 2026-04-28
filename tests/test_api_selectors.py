from __future__ import annotations

import json
from types import SimpleNamespace
from unittest import mock

from app import create_app
from app.agents.agent_types import AgentResponse, StreamingAgentResponse
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
        messages = [
            {"role": "user", "content": "What is retrieval augmented generation?"}
        ]

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

    def test_chat_stream_route_streams_chunks(self):
        with mock.patch(
            "app.api.api_selectors.get_streaming_agent"
        ) as mock_get_streaming_agent:
            mock_get_streaming_agent.return_value = lambda request: StreamingAgentResponse(
                stream=iter(["Hello", " world"])
            )

            response = self.app.test_client().post(
                "/api/chat-stream",
                data=json.dumps(
                    {
                        "messages": [{"role": "user", "content": "Hi there"}],
                        "agent": "linkedin",
                        "query": "Hi there",
                    }
                ),
                content_type="application/json",
            )

            assert response.status_code == 200
            assert response.mimetype == "text/plain"
            assert response.get_data(as_text=True) == "Hello world"

    def test_chat_stream_route_sets_sources_header_for_rag(self):
        sources = [
            {
                "title": "Example Doc",
                "url": "https://example.com/docs/rag",
                "score": 0.92,
            }
        ]

        with mock.patch(
            "app.api.api_selectors.get_streaming_agent"
        ) as mock_get_streaming_agent:
            mock_get_streaming_agent.return_value = lambda request: StreamingAgentResponse(
                stream=iter(["Hello"]),
                sources=sources,
            )

            response = self.app.test_client().post(
                "/api/chat-stream",
                data=json.dumps(
                    {
                        "messages": [{"role": "user", "content": "Tell me about RAG"}],
                        "agent": "rag",
                        "query": "Tell me about RAG",
                    }
                ),
                content_type="application/json",
            )

            assert response.status_code == 200
            assert response.mimetype == "text/plain"
            assert json.loads(response.headers["X-Chat-Sources"]) == sources
            assert response.get_data(as_text=True) == "Hello"

    def test_chat_stream_route_omits_sources_header_when_absent(self):
        with mock.patch(
            "app.api.api_selectors.get_streaming_agent"
        ) as mock_get_streaming_agent:
            mock_get_streaming_agent.return_value = lambda request: StreamingAgentResponse(
                stream=iter(["Hello"])
            )

            response = self.app.test_client().post(
                "/api/chat-stream",
                data=json.dumps(
                    {
                        "messages": [{"role": "user", "content": "Hi there"}],
                        "agent": "linkedin",
                        "query": "Hi there",
                    }
                ),
                content_type="application/json",
            )

            assert response.status_code == 200
            assert response.mimetype == "text/plain"
            assert "X-Chat-Sources" not in response.headers
            assert response.get_data(as_text=True) == "Hello"

    def test_chat_route_returns_sources_for_rag(self):
        with mock.patch("app.api.api_selectors.get_agent") as mock_get_agent:
            mock_get_agent.return_value = lambda request: AgentResponse(
                agent="rag",
                content="RAG answer",
                context=[{"index": 0, "score": 0.92, "text": "Context snippet"}],
                sources=[
                    {
                        "title": "Example Doc",
                        "url": "https://example.com/docs/rag",
                        "score": 0.92,
                    }
                ],
            )

            response = self.app.test_client().post(
                "/api/chat",
                data=json.dumps(
                    {
                        "messages": [{"role": "user", "content": "Tell me about RAG"}],
                        "agent": "rag",
                        "query": "Tell me about RAG",
                    }
                ),
                content_type="application/json",
            )

            assert response.status_code == 200
            assert response.get_json() == {
                "agent": "rag",
                "response": "RAG answer",
                "context": [{"index": 0, "score": 0.92, "text": "Context snippet"}],
                "sources": [
                    {
                        "title": "Example Doc",
                        "url": "https://example.com/docs/rag",
                        "score": 0.92,
                    }
                ],
            }

    def test_chat_route_omits_sources_for_linkedin(self):
        with mock.patch("app.api.api_selectors.get_agent") as mock_get_agent:
            mock_get_agent.return_value = lambda request: AgentResponse(
                agent="linkedin",
                content="LinkedIn answer",
            )

            response = self.app.test_client().post(
                "/api/chat",
                data=json.dumps(
                    {
                        "messages": [{"role": "user", "content": "Write a post"}],
                        "agent": "linkedin",
                        "query": "Write a post",
                    }
                ),
                content_type="application/json",
            )

            assert response.status_code == 200
            assert response.get_json() == {
                "agent": "linkedin",
                "response": "LinkedIn answer",
                "context": [],
            }
            assert "sources" not in response.get_json()

    def test_chat_stream_route_rejects_invalid_agent(self):
        with mock.patch("app.api.api_selectors.get_streaming_agent") as mock_get_agent:
            response = self.app.test_client().post(
                "/api/chat-stream",
                data=json.dumps(
                    {
                        "messages": [{"role": "user", "content": "Hi there"}],
                        "agent": "invalid",
                        "query": "Hi there",
                    }
                ),
                content_type="application/json",
            )

            assert response.status_code == 400
            assert response.get_json() == {
                "error": "agent must be one of linkedin or rag"
            }
            mock_get_agent.assert_not_called()

    def test_index_route_renders_chat_shell_and_scripts(self):
        response = self.app.test_client().get("/")

        body = response.get_data(as_text=True)

        assert response.status_code == 200
        assert 'id="chat-form"' in body
        assert 'id="messages-area"' in body
        assert "/static/js/chat_api.js" in body
        assert "/static/js/chat_renderer.js" in body
        assert "/static/js/chat.js" in body
