from __future__ import annotations

import os

import pytest

from app import create_app


pytestmark = pytest.mark.live_openai


class TestApiSelectorsLive:
    def setup_method(self):
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY is required for live_openai tests")

        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def teardown_method(self):
        if hasattr(self, "app_context"):
            self.app_context.pop()

    def test_select_agent_route_returns_required_fields_and_valid_agent(self):
        response = self.app.test_client().post(
            "/api/select-agent",
            json={
                "messages": [
                    {
                        "role": "user",
                        "content": "Please help me write a concise LinkedIn post about shipping a new feature.",
                    }
                ]
            },
        )

        assert response.status_code == 200

        payload = response.get_json()
        assert isinstance(payload, dict)
        assert "agent" in payload
        assert "query" in payload
        assert payload["agent"] in {"linkedin", "rag"}
        assert isinstance(payload["query"], str)
        assert payload["query"].strip() != ""

    def test_select_agent_route_contract_holds_across_repeated_runs(self):
        messages = [
            {
                "role": "user",
                "content": "How do hooks work in React?",
            }
        ]

        for _ in range(3):
            response = self.app.test_client().post(
                "/api/select-agent",
                json={"messages": messages},
            )

            assert response.status_code == 200
            payload = response.get_json()
            assert isinstance(payload, dict)
            assert payload.get("agent") in {"linkedin", "rag"}
            assert isinstance(payload.get("query"), str)
            assert payload["query"].strip() != ""
