from decimal import Decimal

from app.backend.scrapers.base import BaseScraper, ScrapedProduct
from app.backend.scrapers.registry import scraper_registry
from app.backend.core.logging import get_logger

logger = get_logger(__name__)


@scraper_registry.register
class TapAzScraper(BaseScraper):
    store_slug = "tap_az"
    store_name = "Tap.az"
    base_url = "https://tap.az"

    GRAPHQL_URL = "https://tap.az/graphql"
    GRAPHQL_QUERY = """
    {
        ads(keywords: "%s", first: %d, source: DESKTOP) {
            nodes {
                id
                title
                price
                path
                region
                photo {
                    url
                }
                shop {
                    id
                }
            }
        }
    }
    """

    @staticmethod
    def _is_relevant(title: str, query: str) -> bool:
        query_words = query.lower().split()
        title_lower = title.lower()
        matched = sum(1 for w in query_words if w in title_lower)
        return matched >= len(query_words) * 0.6

    async def search(self, query: str, max_results: int = 10) -> list[ScrapedProduct]:
        client = await self._get_client()
        safe_query = query.replace('"', '\\"')
        # Fetch extra results to compensate for filtering
        fetch_count = max_results * 3
        graphql_query = self.GRAPHQL_QUERY % (safe_query, fetch_count)

        response = await client.post(
            self.GRAPHQL_URL,
            json={"query": graphql_query},
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        response.raise_for_status()
        data = response.json()

        products = []
        nodes = data.get("data", {}).get("ads", {}).get("nodes", [])
        for node in nodes:
            title = node.get("title", "")
            if not title:
                continue

            price_val = node.get("price")
            if not price_val:
                continue

            try:
                price = Decimal(str(price_val)).quantize(Decimal("0.01"))
            except Exception:
                continue
            if price <= 0:
                continue

            path = node.get("path", "")
            product_url = f"{self.base_url}{path}" if path else ""

            photo = node.get("photo", {})
            image_url = photo.get("url") if photo else None

            if not self._is_relevant(title, query):
                continue

            shop = node.get("shop")
            is_shop = shop and shop.get("id")
            display_name = f"[Mağaza] {title}" if is_shop else title

            products.append(ScrapedProduct(
                product_name=display_name,
                price=price,
                product_url=product_url,
                store_slug=self.store_slug,
                store_name=self.store_name,
                image_url=image_url,
            ))

            if len(products) >= max_results:
                break

        return products
