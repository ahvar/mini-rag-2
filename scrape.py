from app.index_pipeline import load_environment
from bs4 import SoupStrainer
from langchain_community.document_loaders import WebBaseLoader
import asyncio

load_environment()

async def main(urls=None):
    if urls is None:
        urls = ["https://react.dev/learn"]
    loader = WebBaseLoader(
        web_paths=urls,
        requests_per_second=1,
        bs_kwargs={
            "parse_only": SoupStrainer(class_=(
                "post-content",
                "post-title",
                "post-header",
                "content",
                "article",
                "article-content",
                "markdown-body",
                "main",
                "docs-wrapper",
                "docs-content",
            )),
        },
    )
    documents = await asyncio.to_thread(loader.load)
    print(documents)

if __name__ == "__main__":
    asyncio.run(main())
