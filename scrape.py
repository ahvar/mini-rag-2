from app.index_pipeline import load_environment
from bs4 import SoupStrainer
from langchain_community.document_loaders import WebBaseLoader
import asyncio

load_environment()

async def main(urls=None):
    if urls is None:
        urls = ["https://react.dev/learn"]

    # Use sync load in a worker thread because WebBaseLoader.aload() internally
    # calls asyncio.run(), which breaks when the caller already has an event loop.
    loader = WebBaseLoader(
        web_paths=urls,
        requests_per_second=1,
    )
    documents = await asyncio.to_thread(loader.load)

    # Fallback: if page content is empty, retry with semantic tag filtering.
    if all(not doc.page_content.strip() for doc in documents):
        loader = WebBaseLoader(
            web_paths=urls,
            requests_per_second=1,
            bs_kwargs={"parse_only": SoupStrainer(["main", "article"])},
        )
        documents = await asyncio.to_thread(loader.load)

    print(documents)

if __name__ == "__main__":
    asyncio.run(main())
