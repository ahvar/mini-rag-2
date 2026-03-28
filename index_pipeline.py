from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any, Iterable, Sequence
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone
from polite_scraper import DEFAULT_URLS, Scraper
from text_chunker import TextChunker, IndexedChunk

ROOT_DIR = Path(__file__).resolve().parents[2]

DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_EMBEDDING_DIMENSIONS = 512
DEFAULT_BATCH_SIZE = 100


def load_environment() -> None:
    """Load local environment variables for OpenAI and Pinecone clients."""
    env_local_path = ROOT_DIR / ".env.local"
    env_path = ROOT_DIR / ".env"

    if env_local_path.exists():
        load_dotenv(env_local_path)
    elif env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()


class IndexingPipeline:
    """Offline-style indexing flow: load, preprocess, embed, and upsert."""

    def __init__(
        self,
        scraper: Scraper,
        chunker: TextChunker,
        batch_size: int = DEFAULT_BATCH_SIZE,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
        embedding_dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS,
    ) -> None:
        load_environment()
        self.scraper = scraper
        self.chunker = chunker
        self.batch_size = batch_size
        self.embedding_model = embedding_model
        self.embedding_dimensions = embedding_dimensions
        self.index_name = os.environ["PINECONE_INDEX"]
        self.embeddings = OpenAIEmbeddings(
            model=embedding_model,
            dimensions=embedding_dimensions,
        )
        self.index = Pinecone(api_key=os.environ["PINECONE_API_KEY"]).Index(
            self.index_name
        )

    async def index_urls(self, urls: Sequence[str]) -> list[IndexedChunk]:
        print("Starting content scraping and vectorization...")
        print(f"Started at: {asyncio.get_running_loop().time():.3f}")
        print("\n🧭 Indexing stages:")
        print("1. Web loading and crawling")
        print("2. Preprocessing and recursive chunking")
        print("3. Embedding and indexing")
        print("4. Upserting vectors into Pinecone")

        documents = await self.scraper.load(urls)
        if not documents:
            print("No documents found to process.")
            return []

        chunks = self.chunker.chunk_documents(documents)
        print(
            f"\n✂️ Created {len(chunks)} chunks with chunk size {self.chunker.chunk_size}."
        )

        await self._embed_and_upsert(chunks)
        print("\n✅ Indexing pipeline completed.")
        return chunks

    async def _embed_and_upsert(self, chunks: Sequence[IndexedChunk]) -> None:
        total_batches = (len(chunks) + self.batch_size - 1) // self.batch_size
        success_count = 0
        fail_count = 0

        for batch_number, start_index in enumerate(
            range(0, len(chunks), self.batch_size), start=1
        ):
            batch = list(chunks[start_index : start_index + self.batch_size])
            print(f"\n🔄 Processing batch {batch_number}/{total_batches}...")
            try:
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
                await asyncio.to_thread(self.index.upsert, vectors=vectors)
                success_count += len(batch)
                print(f"✅ Uploaded {len(batch)} vectors")
            except Exception as exc:  # noqa: BLE001
                fail_count += len(batch)
                print(f"❌ Failed batch {batch_number}: {exc}")

        print("\n📊 SUMMARY")
        print("==================")
        print(f"Total chunks: {len(chunks)}")
        print(f"Successful: {success_count}")
        print(f"Failed: {fail_count}")


async def main(urls: Iterable[str] | None = None) -> None:
    selected_urls = list(urls or DEFAULT_URLS)
    scraper = Scraper()
    chunker = TextChunker(chunk_size=100, chunk_overlap=20)
    pipeline = IndexingPipeline(scraper=scraper, chunker=chunker)
    await pipeline.index_urls(selected_urls)


if __name__ == "__main__":
    asyncio.run(main())
