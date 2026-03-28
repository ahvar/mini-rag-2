import asyncio
from unittest import mock

from index_pipeline import IndexingPipeline


class TestIndexPipeline:
    def test_index_urls_embeddings_and_upsert_are_fully_mocked(
        self,
        mock_openai_embeddings,
        mock_pinecone,
        mock_index_pipeline_environment,
    ):
        MockOpenAIEmbeddings, embeddings_instance = mock_openai_embeddings
        MockPinecone, pinecone_client, index_instance = mock_pinecone

        scraper = mock.Mock(name="Scraper")
        scraper.load = mock.AsyncMock(
            return_value=[mock.Mock(page_content="doc", metadata={"url": "https://example.com"})]
        )

        chunk = mock.Mock(
            id="chunk-1",
            content="hello world",
            metadata={"url": "https://example.com", "chunkIndex": 0},
        )
        chunker = mock.Mock(name="TextChunker")
        chunker.chunk_size = 100
        chunker.chunk_documents.return_value = [chunk]

        embeddings_instance.aembed_documents.return_value = [[0.01, 0.02, 0.03]]

        with mock.patch("index_pipeline.load_environment") as mock_load_environment:
            pipeline = IndexingPipeline(scraper=scraper, chunker=chunker, batch_size=1)

        indexed_chunks = asyncio.run(pipeline.index_urls(["https://example.com"]))

        mock_load_environment.assert_called_once_with()
        MockOpenAIEmbeddings.assert_called_once_with(
            model="text-embedding-3-small",
            dimensions=512,
        )
        MockPinecone.assert_called_once_with(api_key="test-pinecone-key")
        pinecone_client.Index.assert_called_once_with("test-index")

        scraper.load.assert_awaited_once_with(["https://example.com"])
        chunker.chunk_documents.assert_called_once()
        embeddings_instance.aembed_documents.assert_awaited_once_with(["hello world"])
        index_instance.upsert.assert_called_once_with(
            vectors=[
                {
                    "id": "chunk-1",
                    "values": [0.01, 0.02, 0.03],
                    "metadata": {
                        "url": "https://example.com",
                        "chunkIndex": 0,
                        "text": "hello world",
                    },
                }
            ]
        )
        assert indexed_chunks == [chunk]
