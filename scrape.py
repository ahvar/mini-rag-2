from app.index_pipeline import (
    DEFAULT_EMBEDDING_DIMENSIONS,
    DEFAULT_EMBEDDING_MODEL,
    load_environment,
)
from app.polite_scraper import Scraper
from app.text_chunker import TextChunker
from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone
import asyncio
import os

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

    pinecone_index_name = os.environ["PINECONE_INDEX"]
    pinecone_namespace = os.getenv("PINECONE_NAMESPACE")
    index = Pinecone(api_key=os.environ["PINECONE_API_KEY"]).Index(pinecone_index_name)

    vectors = [
        {
            "id": chunk.id,
            "values": embedding,
            "metadata": {
                **chunk.metadata,
                "text": chunk.content,
            },
        }
        for chunk, embedding in zip(chunks, chunk_embeddings, strict=True)
    ]

    upsert_response = await asyncio.to_thread(
        index.upsert,
        vectors=vectors,
        namespace=pinecone_namespace,
    )
    print(f"Pinecone upsert response: {upsert_response}")

    sample_id = chunks[0].id
    fetch_response = await asyncio.to_thread(
        index.fetch,
        ids=[sample_id],
        namespace=pinecone_namespace,
    )
    fetched_vectors = (
        fetch_response.get("vectors", {})
        if isinstance(fetch_response, dict)
        else getattr(fetch_response, "vectors", {})
    )
    was_upserted = sample_id in fetched_vectors
    print(f"Verification fetch for '{sample_id}': upserted={was_upserted}")


if __name__ == "__main__":
    asyncio.run(main())
