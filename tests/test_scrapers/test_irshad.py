from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.backend.scrapers.irshad import IrshadScraper


@pytest.mark.asyncio
async def test_irshad_html_parsing(irshad_html):
    scraper = IrshadScraper()

    with patch.object(scraper, "_get_page", new_callable=AsyncMock, return_value=irshad_html):
        with patch.object(scraper, "_delay", new_callable=AsyncMock):
            results = await scraper.search("iphone 15")

    assert len(results) == 1
    assert results[0].product_name == "Apple iPhone 15 128GB"
    assert results[0].price == Decimal("1799.00")
    assert results[0].store_slug == "irshad"
