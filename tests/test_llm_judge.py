from __future__ import annotations

from types import SimpleNamespace
from unittest import mock

from pydantic import ValidationError

from app.main.llm_judge import JudgeResult, RawJudgeResult, judge_response


TEST_CASES = [
    {
        "name": "React hooks explanation",
        "question": "What are React hooks?",
        "golden_response": (
            "React hooks are special functions that allow you to use state and other "
            "React features in functional components. They enable you to manage "
            "component lifecycle and state without needing to convert your "
            "functional components into class components.\n\n"
            "One of the most commonly used hooks is useState, which allows you to "
            "add state to your functional components. There are also other built-in "
            "hooks provided by React, and you can create your own custom hooks by "
            "combining existing ones.\n\n"
            "It's important to note that hooks have certain rules and restrictions "
            "compared to regular functions, such as only being called at the top "
            "level of a component or within other hooks."
        ),
    },
    {
        "name": "React components explanation",
        "question": "What are React components?",
        "golden_response": (
            "React components are the building blocks of a React application. They "
            "are JavaScript functions (or classes) that return markup, typically in "
            "the form of JSX, which describes what the UI should look like. "
            "Components can be as small as a button or as large as an entire page.\n\n"
            "Key points about React components include:\n\n"
            "Naming Convention: React component names must always start with a "
            "capital letter. This helps distinguish them from regular HTML elements.\n"
            "Reusability: Components can be reused throughout your application, "
            "allowing for a modular and maintainable code structure.\n"
            "Composition: You can create complex UIs by nesting components within "
            "one another, enabling a hierarchical structure.\n"
            "State and Props: Components can manage their own state or receive data "
            "through props, allowing for dynamic and interactive UIs.\n"
            "If you have more specific questions about components or how to use "
            "them, feel free to ask!"
        ),
    },
    {
        "name": "Python dataclasses explanation",
        "question": "What are Python dataclasses?",
        "golden_response": (
            "Python dataclasses are a feature introduced in Python 3.7 that provide "
            "a decorator and functions for automatically adding special methods to "
            "classes. They simplify the creation of classes that are primarily used "
            "to store data by automatically generating methods like __init__, "
            "__repr__, __eq__, and others based on class attributes.\n\n"
            "To create a dataclass, you use the @dataclass decorator from the "
            "dataclasses module. Here's a simple example:\n\n"
            "from dataclasses import dataclass\n\n"
            "@dataclass\n"
            "class Point:\n"
            "    x: int\n"
            "    y: int\n\n"
            "In this example, the Point class automatically gets an __init__ method "
            "that takes x and y as parameters, as well as a __repr__ method for easy "
            "string representation and an __eq__ method for comparing instances.\n\n"
            "Dataclasses also support features like default values, default "
            "factories, and immutability (using frozen=True), making them a powerful "
            "tool for managing data in Python."
        ),
    },
]


class TestLlmJudge:
    def test_judge_result_schema_restricts_score_range(self):
        assert JudgeResult(score=8, reason="Solid answer").score == 8

        try:
            JudgeResult(score=11, reason="Out of range")
            assert False, "Expected ValidationError for score > 10"
        except ValidationError:
            assert True

    @mock.patch("app.main.llm_judge.create_openai_client")
    def test_judge_response_uses_structured_output_parse(self, mock_create_client):
        client = mock_create_client.return_value
        client.beta.chat.completions.parse.return_value = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        parsed=RawJudgeResult(score=9, reason="Comprehensive")
                    )
                )
            ]
        )

        result = judge_response(
            question="What are React hooks?",
            actual_response="They manage state in function components.",
            golden_response=TEST_CASES[0]["golden_response"],
        )

        assert result.score == 9
        assert result.reason == "Comprehensive"

        client.beta.chat.completions.parse.assert_called_once()
        _, kwargs = client.beta.chat.completions.parse.call_args
        assert kwargs["response_format"] is RawJudgeResult
        assert kwargs["temperature"] == 0

    @mock.patch("app.main.llm_judge.create_openai_client")
    def test_golden_responses_are_used_in_judge_prompt(self, mock_create_client):
        client = mock_create_client.return_value
        client.beta.chat.completions.parse.return_value = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        parsed=RawJudgeResult(score=9, reason="High quality")
                    )
                )
            ]
        )

        passing_score = 8

        for case in TEST_CASES:
            result = judge_response(
                question=case["question"],
                actual_response="placeholder",
                golden_response=case["golden_response"],
            )
            assert result.score >= passing_score, case["name"]

        assert client.beta.chat.completions.parse.call_count == len(TEST_CASES)
        for call, case in zip(client.beta.chat.completions.parse.call_args_list, TEST_CASES):
            _, kwargs = call
            user_prompt = kwargs["messages"][1]["content"]
            assert case["question"] in user_prompt
            assert case["golden_response"] in user_prompt

    @mock.patch("app.main.llm_judge.create_openai_client")
    def test_judge_response_caps_score_above_ten(self, mock_create_client):
        client = mock_create_client.return_value
        client.beta.chat.completions.parse.return_value = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        parsed=RawJudgeResult(score=12, reason="Better than reference")
                    )
                )
            ]
        )

        result = judge_response(
            question="What are React hooks?",
            actual_response="Detailed and accurate response",
            golden_response=TEST_CASES[0]["golden_response"],
        )
        assert result.score == 10
