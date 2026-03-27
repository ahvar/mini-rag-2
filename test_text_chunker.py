from __future__ import annotations

from functools import partial
from unittest import mock

import pytest

pytest.importorskip("langchain_core.documents")
pytest.importorskip("langchain_text_splitters")

import text_chunker
from text_chunker import TextChunker


def make_mock_document(page_content: str, metadata: dict | None = None):
    document = mock.Mock(name="DocumentInstance")
    document.page_content = page_content
    document.metadata = metadata or {}
    return document


def split_documents_using_splitter(documents, splitter_instance):
    split_docs = []
    step = max(1, splitter_instance.chunk_size - splitter_instance.chunk_overlap)

    for document in documents:
        text = document.page_content
        if len(text) <= splitter_instance.chunk_size:
            split_docs.append(make_mock_document(text, dict(document.metadata)))
            continue

        for start in range(0, len(text), step):
            chunk_text = text[start : start + splitter_instance.chunk_size]
            if not chunk_text:
                continue
            split_docs.append(make_mock_document(chunk_text, dict(document.metadata)))
            if start + splitter_instance.chunk_size >= len(text):
                break

    return split_docs


@pytest.fixture
def mock_document():
    return make_mock_document


@pytest.fixture
def mock_splitter():
    MockSplitter = mock.Mock(name="RecursiveCharacterTextSplitter")

    with mock.patch.object(
        text_chunker,
        "RecursiveCharacterTextSplitter",
        MockSplitter,
    ):
        splitter_instance = MockSplitter.return_value

        def configure_splitter(
            chunk_size: int,
            chunk_overlap: int,
            length_function,
            is_separator_regex: bool,
        ):
            splitter_instance.chunk_size = chunk_size
            splitter_instance.chunk_overlap = chunk_overlap
            splitter_instance.length_function = length_function
            splitter_instance.is_separator_regex = is_separator_regex
            return splitter_instance

        MockSplitter.side_effect = configure_splitter
        splitter_instance.split_documents.side_effect = partial(
            split_documents_using_splitter,
            splitter_instance=splitter_instance,
        )

        yield MockSplitter, splitter_instance


class TestTextChunker:
    def test_chunker_uses_configured_mock_splitter(self, mock_document, mock_splitter):
        input_documents = [
            mock_document(
                page_content="abcdefghijklmnop",
                metadata={"source": "https://example.com"},
            )
        ]

        MockSplitter, splitter_instance = mock_splitter
        chunker = TextChunker(chunk_size=8, chunk_overlap=2)
        chunks = chunker.chunk_documents(input_documents)

        MockSplitter.assert_called_once_with(
            chunk_size=8,
            chunk_overlap=2,
            length_function=len,
            is_separator_regex=False,
        )
        splitter_instance.split_documents.assert_called_once_with(input_documents)

        assert [chunk.content for chunk in chunks] == ["abcdefgh", "ghijklmn", "mnop"]
        assert [chunk.metadata["chunkIndex"] for chunk in chunks] == [0, 1, 2]
        assert all(chunk.metadata["totalChunks"] == 3 for chunk in chunks)
