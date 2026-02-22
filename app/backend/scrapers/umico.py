from decimal import Decimal

from app.backend.scrapers.base import BaseScraper, ScrapedProduct
from app.backend.scrapers.registry import scraper_registry
from app.backend.core.logging import get_logger

logger = get_logger(__name__)


@scraper_registry.register
class UmicoScraper(BaseScraper):
    store_slug = "umico"
    store_name = "Birmarket"
    base_url = "https://birmarket.az"

    SUGGESTS_API = "https://mp-catalog.umico.az/api/v1/suggests"

    async def search(self, query: str, max_results: int = 10) -> list[ScrapedProduct]:
        client = await self._get_client()
        response = await client.get(
            self.SUGGESTS_API,
            params={"full_text": query, "per_page": str(max_results)},
            headers={
                "Accept": "application/json",
                "Accept-Language": "az,en;q=0.9",
            },
        )
        response.raise_for_status()
        data = response.json()

        products = []
        items = data.get("products", [])
        for item in items[:max_results]:
            name = item.get("name", "")
            if not name:
                continue

            pid = item.get("id")
            slug = item.get("slugged_name", "")
            price_val = item.get("retail_price")
            if not price_val:
                continue

            try:
                price = Decimal(str(price_val)).quantize(Decimal("0.01"))
            except Exception:
                continue
            if price <= 0:
                continue

            img_data = item.get("main_img", {})
            image_url = img_data.get("medium") or img_data.get("small") or img_data.get("big")

            product_url = f"{self.base_url}/product/{pid}-{slug}" if pid and slug else ""

            products.append(ScrapedProduct(
                product_name=name,
                price=price,
                product_url=product_url,
                store_slug=self.store_slug,
                store_name=self.store_name,
                image_url=image_url,
            ))

        return products
