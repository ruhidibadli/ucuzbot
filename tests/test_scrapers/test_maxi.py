from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.backend.scrapers.maxi import MaxiScraper


@pytest.mark.asyncio
async def test_maxi_html_parsing(maxi_html):
    scraper = MaxiScraper()

    with patch.object(scraper, "_get_page", new_callable=AsyncMock, return_value=maxi_html):
        with patch.object(scraper, "_delay", new_callable=AsyncMock):
            results = await scraper.search("iphone 15")

    assert len(results) == 1
    assert results[0].product_name == "iPhone 15 128GB"
    assert results[0].price == Decimal("1820.00")
    assert results[0].store_slug == "maxi"


@pytest.mark.asyncio
async def test_maxi_maintenance_page(maxi_maintenance_html):
    scraper = MaxiScraper()

    with patch.object(scraper, "_get_page", new_callable=AsyncMock, return_value=maxi_maintenance_html):
        results = await scraper.search("iphone 15")

    assert results == []


@pytest.mark.asyncio
async def test_maxi_site_down():
    scraper = MaxiScraper()

    with patch.object(scraper, "_get_page", side_effect=Exception("Connection refused")):
        results = await scraper.search("iphone 15")

    assert results == []
