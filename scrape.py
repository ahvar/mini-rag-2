from app.index_pipeline import (
    DEFAULT_EMBEDDING_DIMENSIONS,
    DEFAULT_EMBEDDING_MODEL,
    load_environment,
)
from app.polite_scraper import Scraper
from app.text_chunker import TextChunker
from langchain_openai import OpenAIEmbeddings
import asyncio

load_environment()


async def main(urls=None):
    if urls is None:
        urls = [
            "https://react.dev/learn",
            "https://lilianweng.github.io/posts/2023-06-23-agent/",
        ]

    scraper = Scraper(
        max_concurrency=1,
        requests_per_second=1,
        crawl_delay_seconds=0.0,
    )
    documents = await scraper.load(urls)

    chunker = TextChunker()
    chunks = chunker.chunk_documents(documents)

    print(f"Total chunks for embedding: {len(chunks)}")
    for chunk in chunks:
        print(chunk)

    embeddings_client = OpenAIEmbeddings(
        model=DEFAULT_EMBEDDING_MODEL,
        dimensions=DEFAULT_EMBEDDING_DIMENSIONS,
    )
    chunk_embeddings = await embeddings_client.aembed_documents(
        [chunk.content for chunk in chunks]
    )

    print(f"Generated {len(chunk_embeddings)} embeddings")
    for index, embedding in enumerate(chunk_embeddings):
        print(f"chunk[{index}] embedding dimensions: {len(embedding)}")


if __name__ == "__main__":
    asyncio.run(main())
