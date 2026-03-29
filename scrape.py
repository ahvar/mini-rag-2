from app.polite_scraper import Scraper
from app.index_pipeline import load_environment
from typing import Iterable

urls = ["https://react.dev/learn"]


async def main(urls: Iterable[str] | None = None) -> None:
    selected_urls = list(urls)
    scraper = Scraper()
    documents = await scraper.load(urls)
    print(documents)
