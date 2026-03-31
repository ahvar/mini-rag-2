from app.index_pipeline import load_environment
from app.polite_scraper import Scraper
import asyncio

load_environment()

async def main(urls=None):
    if urls is None:
        urls = ["https://react.dev/learn", "https://lilianweng.github.io/posts/2023-06-23-agent/"]

    scraper = Scraper(
        max_concurrency=1,
        requests_per_second=1,
        crawl_delay_seconds=0.0,
    )
    documents = await scraper.load(urls)

    print(documents)

if __name__ == "__main__":
    asyncio.run(main())
