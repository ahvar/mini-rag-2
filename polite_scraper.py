from typing import Sequence
import asyncio
from bs4 import SoupStrainer
from langchain_core.documents import Document
from langchain_community.document_loaders import WebBaseLoader

DEFAULT_MAX_CONCURRENCY = 2
DEFAULT_REQUESTS_PER_SECOND = 1
DEFAULT_CRAWL_DELAY_SECONDS = 1.0
DEFAULT_PARSE_CLASSES = (
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
)
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


class Scraper:
    """Asynchronously fetch and clean web content with polite rate limiting."""

    def __init__(
        self,
        max_concurrency: int = DEFAULT_MAX_CONCURRENCY,
        requests_per_second: int = DEFAULT_REQUESTS_PER_SECOND,
        crawl_delay_seconds: float = DEFAULT_CRAWL_DELAY_SECONDS,
        parse_classes: Sequence[str] = DEFAULT_PARSE_CLASSES,
    ) -> None:
        self.max_concurrency = max(1, max_concurrency)
        self.requests_per_second = max(1, requests_per_second)
        self.crawl_delay_seconds = max(0.0, crawl_delay_seconds)
        self.semaphore = asyncio.Semaphore(self.max_concurrency)
        self.parse_classes = tuple(parse_classes)

    async def load(self, urls: Sequence[str]) -> list[Document]:
        tasks = [
            asyncio.create_task(self._load_single_url(url=url, position=index))
            for index, url in enumerate(urls)
        ]
        loaded_documents: list[Document] = []

        for task in asyncio.as_completed(tasks):
            documents = await task
            loaded_documents.extend(documents)

        return loaded_documents

    async def _load_single_url(self, url: str, position: int) -> list[Document]:
        await asyncio.sleep(position * self.crawl_delay_seconds)

        async with self.semaphore:
            print(f"📥 Loading {url}")
            loader = WebBaseLoader(
                web_paths=(url,),
                requests_per_second=self.requests_per_second,
                bs_kwargs={
                    "parse_only": SoupStrainer(class_=self.parse_classes),
                },
            )

            if hasattr(loader, "aload"):
                documents = await loader.aload()
            else:
                documents = await asyncio.to_thread(loader.load)

            cleaned_documents = [
                self._normalize_document(document, url) for document in documents
            ]
            print(f"✅ Loaded {url}: {len(cleaned_documents)} document(s)")
            return cleaned_documents

    @staticmethod
    def _normalize_document(document: Document, url: str) -> Document:
        cleaned_content = " ".join(document.page_content.split())
        metadata = {
            **document.metadata,
            "url": url,
            "source": url,
            "title": document.metadata.get("title") or url,
        }
        return Document(page_content=cleaned_content, metadata=metadata)
