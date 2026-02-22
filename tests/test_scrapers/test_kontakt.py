from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.backend.scrapers.kontakt import KontaktScraper


@pytest.mark.asyncio
async def test_kontakt_html_parsing(kontakt_html):
    scraper = KontaktScraper()

    with patch.object(scraper, "_search_api", return_value=[]):
        with patch.object(scraper, "_get_page", new_callable=AsyncMock, return_value=kontakt_html):
            with patch.object(scraper, "_delay", new_callable=AsyncMock):
                results = await scraper.search("iphone 15")

    assert len(results) == 2
    assert results[0].product_name == "Apple iPhone 15 128GB Black"
    assert results[0].price == Decimal("1799.00")
    assert results[0].store_slug == "kontakt"
    assert "iphone-15-128gb" in results[0].product_url


@pytest.mark.asyncio
async def test_kontakt_safe_search_handles_error():
    scraper = KontaktScraper()

    with patch.object(scraper, "search", side_effect=Exception("Connection error")):
        results = await scraper.safe_search("iphone")

    assert results == []
