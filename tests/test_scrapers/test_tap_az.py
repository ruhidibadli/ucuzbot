from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.backend.scrapers.tap_az import TapAzScraper


@pytest.mark.asyncio
async def test_tap_az_html_parsing(tap_az_html):
    scraper = TapAzScraper()

    with patch.object(scraper, "_get_page", new_callable=AsyncMock, return_value=tap_az_html):
        with patch.object(scraper, "_delay", new_callable=AsyncMock):
            results = await scraper.search("iphone 15")

    assert len(results) == 2
    assert results[0].price == Decimal("1650.00")
    assert results[0].store_slug == "tap_az"
    # Second result should have shop badge
    assert "[Mağaza]" in results[1].product_name
