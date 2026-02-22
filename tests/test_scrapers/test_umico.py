from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.backend.scrapers.umico import UmicoScraper


@pytest.mark.asyncio
async def test_umico_html_parsing(umico_html):
    scraper = UmicoScraper()

    with patch.object(scraper, "_search_api", return_value=[]):
        with patch.object(scraper, "_get_page", new_callable=AsyncMock, return_value=umico_html):
            with patch.object(scraper, "_delay", new_callable=AsyncMock):
                results = await scraper.search("iphone 15")

    assert len(results) == 1
    assert results[0].product_name == "Apple iPhone 15 128GB"
    assert results[0].price == Decimal("1750.00")
    assert results[0].store_slug == "umico"
