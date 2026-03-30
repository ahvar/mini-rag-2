from app.index_pipeline import load_environment
from bs4 import SoupStrainer
from langchain_community.document_loaders import WebBaseLoader
import asyncio

load_environment()

async def main(urls=None):
    if urls is None:
        urls = ["https://react.dev/learn"]

    # Prefer semantic containers first; many React.dev pages render content here.
    loader = WebBaseLoader(
        web_paths=urls,
        requests_per_second=1,
        bs_kwargs={"parse_only": SoupStrainer(["main", "article"])},
    )
    documents = await loader.aload()

    # Fallback to parsing the full document if the filtered parse returns empty content.
    if all(not doc.page_content.strip() for doc in documents):
        loader = WebBaseLoader(web_paths=urls, requests_per_second=1)
        documents = await loader.aload()

    print(documents)

if __name__ == "__main__":
    asyncio.run(main())
