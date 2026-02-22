from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.backend.scrapers.baku_electronics import BakuElectronicsScraper


@pytest.mark.asyncio
async def test_baku_electronics_html_parsing(baku_electronics_html):
    scraper = BakuElectronicsScraper()

    with patch.object(scraper, "_get_page", new_callable=AsyncMock, return_value=baku_electronics_html):
        with patch.object(scraper, "_delay", new_callable=AsyncMock):
            results = await scraper.search("iphone 15")

    assert len(results) == 2
    assert results[0].product_name == "iPhone 15 128GB"
    assert results[0].price == Decimal("1749.00")
    assert results[0].store_slug == "baku_electronics"
    assert results[1].price == Decimal("2899.00")
