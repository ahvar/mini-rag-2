import asyncio

from langchain_openai import OpenAIEmbeddings

from app.main.index_pipeline import DEFAULT_EMBEDDING_DIMENSIONS, DEFAULT_EMBEDDING_MODEL
from app.main.pinecone_client import PineconeClient
from app.main.polite_scraper import Scraper
from app.main.text_chunker import TextChunker
from config import Config


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

    embeddings_client = OpenAIEmbeddings(
        model=DEFAULT_EMBEDDING_MODEL,
        dimensions=DEFAULT_EMBEDDING_DIMENSIONS,
        api_key=Config.OPENAI_API_KEY,
    )
    chunk_embeddings = await embeddings_client.aembed_documents(
        [chunk.content for chunk in chunks]
    )

    pinecone_client = PineconeClient(
        api_key=Config.PINECONE_API_KEY,
        index_name=Config.PINECONE_INDEX,
        namespace=Config.PINECONE_NAMESPACE,
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
        for chunk, embedding in zip(chunks, chunk_embeddings, strict=True)
    ]

    upsert_response = await pinecone_client.upsert_vectors(vectors)
    print(f"Pinecone upsert response: {upsert_response}")

    sample_id = chunks[0].id
    fetch_response = await pinecone_client.fetch_vectors(ids=[sample_id])
    fetched_vectors = (
        fetch_response.get("vectors", {})
        if isinstance(fetch_response, dict)
        else getattr(fetch_response, "vectors", {})
    )
    was_upserted = sample_id in fetched_vectors
    print(f"Verification fetch for '{sample_id}': upserted={was_upserted}")


if __name__ == "__main__":
    asyncio.run(main())
