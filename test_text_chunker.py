from __future__ import annotations
import text_chunker
from unittest import mock
from mock import MagicMock
from text_chunker import TextChunker


class FakeDocument:
    def __init__(self, page_content: str, metadata: dict | None = None) -> None:
        self.page_content = page_content
        self.metadata = metadata or {}


class FakeRecursiveCharacterTextSplitter:
    def __init__(
        self,
        chunk_size: int,
        chunk_overlap: int,
        length_function,
        is_separator_regex: bool,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.length_function = length_function
        self.is_separator_regex = is_separator_regex

    def split_documents(self, documents: list[FakeDocument]) -> list[FakeDocument]:
        split_docs: list[FakeDocument] = []
        step = max(1, self.chunk_size - self.chunk_overlap)

        for document in documents:
            text = document.page_content
            if len(text) <= self.chunk_size:
                split_docs.append(FakeDocument(text, dict(document.metadata)))
                continue

            for start in range(0, len(text), step):
                chunk_text = text[start : start + self.chunk_size]
                if not chunk_text:
                    continue
                split_docs.append(FakeDocument(chunk_text, dict(document.metadata)))
                if start + self.chunk_size >= len(text):
                    break

        return split_docs


class TestTextChunker:
    def setup_method(self):
        self.input_documents = [
            FakeDocument(
                page_content="abcdefghijklmnop",
                metadata={"source": "https://example.com"},
            )
        ]

    def test_chunker(self):
        with mock.patch.object(
            text_chunker,
            "RecursiveCharacterTextSplitter",
        ) as MockSplitter:
            # configure mock here
            print()
            print(f"class: {MockSplitter}")
            print(f"return value: {MockSplitter.return_value}")

            chunker = TextChunker(chunk_size=8, chunk_overlap=2)
            chunks = chunker.chunk_documents(self.input_documents)
