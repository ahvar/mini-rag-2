import asyncio
from unittest import mock

from app.main.index_pipeline import IndexingPipeline


class TestIndexPipeline:

    def setup_method(self):
        self.scraper = mock.Mock(name="Scraper")
        self.scraper.load = mock.AsyncMock(
            return_value=[
                mock.Mock(page_content="doc", metadata={"url": "https://example.com"})
            ]
        )
        self.chunker = mock.Mock(name="TextChunker")
        self.chunker.chunk_size = 100

    def test_index_urls(
        self,
        mock_openai_embeddings,
    ):
        MockOpenAIEmbeddings, embeddings_instance = mock_openai_embeddings

        chunk = mock.Mock(
            id="chunk-1",
            content="hello world",
            metadata={"url": "https://example.com", "chunkIndex": 0},
        )
        self.chunker.chunk_documents.return_value = [chunk]

        embeddings_instance.aembed_documents.return_value = [[0.01, 0.02, 0.03]]
        pinecone_client = mock.Mock(name="PineconeClient")
        pinecone_client.upsert_vectors = mock.AsyncMock(name="upsert_vectors")

        pipeline = IndexingPipeline(
            scraper=self.scraper,
            chunker=self.chunker,
            pinecone_client=pinecone_client,
            batch_size=1,
        )

        indexed_chunks = asyncio.run(pipeline.index_urls(["https://example.com"]))

        MockOpenAIEmbeddings.assert_called_once_with(
            model="text-embedding-3-small",
            dimensions=512,
            api_key=mock.ANY,
        )
        self.scraper.load.assert_awaited_once_with(["https://example.com"])
        self.chunker.chunk_documents.assert_called_once()
        embeddings_instance.aembed_documents.assert_awaited_once_with(["hello world"])
        pinecone_client.upsert_vectors.assert_awaited_once_with(
            [
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
