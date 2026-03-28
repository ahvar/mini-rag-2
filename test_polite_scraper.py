import asyncio

from polite_scraper import Scraper


class TestPoliteScraper:
    def test_load_single_url_returns_normalized_documents(
        self,
        mock_document,
        mock_web_loader,
        mock_soup_strainer,
    ):
        source_url = "https://example.com/article"
        MockWebBaseLoader, loader_instance = mock_web_loader
        MockSoupStrainer, parse_only = mock_soup_strainer

        loader_instance.aload.return_value = [
            mock_document(
                page_content="  Hello    world\nfrom   scraper.  ",
                metadata={"title": "Example title", "author": "A. Writer"},
            )
        ]

        scraper = Scraper(
            max_concurrency=1,
            requests_per_second=3,
            crawl_delay_seconds=0.0,
        )

        documents = asyncio.run(scraper._load_single_url(url=source_url, position=0))

        MockSoupStrainer.assert_called_once_with(class_=scraper.parse_classes)
        MockWebBaseLoader.assert_called_once_with(
            web_paths=(source_url,),
            requests_per_second=3,
            bs_kwargs={"parse_only": parse_only},
        )
        loader_instance.aload.assert_awaited_once()

        assert len(documents) == 1
        assert documents[0].page_content == "Hello world from scraper."
        assert documents[0].metadata["url"] == source_url
        assert documents[0].metadata["source"] == source_url
        assert documents[0].metadata["title"] == "Example title"
        assert documents[0].metadata["author"] == "A. Writer"
