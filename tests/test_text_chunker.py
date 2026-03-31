from __future__ import annotations

from app.main.text_chunker import TextChunker


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
