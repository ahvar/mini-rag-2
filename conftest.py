import pytest
import text_chunker
from unittest import mock
from functools import partial
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


@pytest.fixture
def mock_document():
    return make_mock_document
