from __future__ import annotations

import asyncio
from typing import Iterable, Sequence

from langchain_openai import OpenAIEmbeddings

from config import Config
from app.main.pinecone_client import PineconeClient
from app.main.polite_scraper import Scraper
from app.main.text_chunker import IndexedChunk, TextChunker

DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_EMBEDDING_DIMENSIONS = 512
DEFAULT_BATCH_SIZE = 100

DEFAULT_URLS = [
    "https://react.dev/learn",
    "https://react.dev/reference/react/useState",
    "https://react.dev/reference/react/useEffect",
    "https://nextjs.org/docs/getting-started",
    "https://nextjs.org/docs/app/building-your-application/routing",
    "https://nextjs.org/docs/app/building-your-application/data-fetching",
    "https://www.typescriptlang.org/docs/handbook/2/basic-types.html",
    "https://sdk.vercel.ai/docs/ai-sdk-core/generating-text",
    "https://github.com/vercel/ai",
    "https://github.com/pinecone-io/pinecone-ts-client",
    "https://lilianweng.github.io/posts/2023-06-23-agent/",
]


class IndexingPipeline:
    """Offline-style indexing flow: load, preprocess, embed, and upsert."""

    def __init__(
        self,
        scraper: Scraper,
        chunker: TextChunker,
        pinecone_client: PineconeClient,
        batch_size: int = DEFAULT_BATCH_SIZE,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
        embedding_dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS,
    ) -> None:
        self.scraper = scraper
        self.chunker = chunker
        self.pinecone_client = pinecone_client
        self.batch_size = batch_size
        self.embedding_model = embedding_model
        self.embedding_dimensions = embedding_dimensions
        self.embeddings = OpenAIEmbeddings(
            model=embedding_model,
            dimensions=embedding_dimensions,
            api_key=Config.OPENAI_API_KEY,
        )

    async def index_urls(self, urls: Sequence[str]) -> list[IndexedChunk]:
        documents = await self.scraper.load(urls)
        if not documents:
            return []

        chunks = self.chunker.chunk_documents(documents)
        await self._embed_and_upsert(chunks)
        return chunks

    async def _embed_and_upsert(self, chunks: Sequence[IndexedChunk]) -> None:
        for start_index in range(0, len(chunks), self.batch_size):
            batch = list(chunks[start_index : start_index + self.batch_size])
            embeddings = await self.embeddings.aembed_documents(
                [chunk.content for chunk in batch]
            )
            vectors = [
                {
                    "id": chunk.id,
                    "values": embedding,
                    "metadata": {
                        **chunk.metadata,
                        "text": chunk.content,
                    },
                }
                for chunk, embedding in zip(batch, embeddings, strict=True)
            ]
            await self.pinecone_client.upsert_vectors(vectors)


async def main(urls: Iterable[str] | None = None) -> None:
    selected_urls = list(urls or DEFAULT_URLS)
    scraper = Scraper()
    chunker = TextChunker(chunk_size=100, chunk_overlap=20)
    pinecone_client = PineconeClient(
        api_key=Config.PINECONE_API_KEY,
        index_name=Config.PINECONE_INDEX,
        namespace=Config.PINECONE_NAMESPACE,
    )
    pipeline = IndexingPipeline(
        scraper=scraper,
        chunker=chunker,
        pinecone_client=pinecone_client,
    )
    await pipeline.index_urls(selected_urls)


if __name__ == "__main__":
    asyncio.run(main())
