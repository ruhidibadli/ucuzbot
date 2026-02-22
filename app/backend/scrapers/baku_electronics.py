import json
from decimal import Decimal
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from app.backend.scrapers.base import BaseScraper, ScrapedProduct
from app.backend.scrapers.registry import scraper_registry
from app.backend.core.logging import get_logger

logger = get_logger(__name__)


@scraper_registry.register
class BakuElectronicsScraper(BaseScraper):
    store_slug = "baku_electronics"
    store_name = "Baku Electronics"
    base_url = "https://www.bakuelectronics.az"

    async def search(self, query: str, max_results: int = 10) -> list[ScrapedProduct]:
        return await self._search_nextjs(query, max_results)

    async def _search_nextjs(self, query: str, max_results: int) -> list[ScrapedProduct]:
        # Baku Electronics uses Next.js. Search results page is at /axtaris-neticesi?name=...
        # Product data is embedded in __NEXT_DATA__ script tag.
        url = f"{self.base_url}/axtaris-neticesi?name={quote_plus(query)}"
        html = await self._get_page(url)
        soup = BeautifulSoup(html, "lxml")

        next_data_tag = soup.find("script", id="__NEXT_DATA__")
        if not next_data_tag or not next_data_tag.string:
            logger.warning("baku_electronics_no_next_data")
            return []

        data = json.loads(next_data_tag.string)
        products_wrapper = (
            data.get("props", {})
            .get("pageProps", {})
            .get("products", {})
            .get("products", {})
        )

        items = products_wrapper.get("items", [])
        if not items:
            return []

        products = []
        for item in items[:max_results]:
            name = item.get("name", "")
            slug = item.get("slug", "")
            price_val = item.get("price", 0)
            discount = item.get("discount", "0")
            image_url = item.get("image", "")

            try:
                price = Decimal(str(price_val)).quantize(Decimal("0.01"))
                # Use discounted price if discount > 0
                if discount and discount != "0":
                    discount_amount = Decimal(str(discount))
                    price = (price - discount_amount).quantize(Decimal("0.01"))
            except Exception:
                continue

            if price <= 0:
                continue

            products.append(ScrapedProduct(
                product_name=name,
                price=price,
                product_url=f"{self.base_url}/mehsul/{slug}",
                store_slug=self.store_slug,
                store_name=self.store_name,
                image_url=image_url if image_url else None,
            ))

        return products
