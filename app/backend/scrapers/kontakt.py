from decimal import Decimal

from app.backend.scrapers.base import BaseScraper, ScrapedProduct
from app.backend.scrapers.registry import scraper_registry
from app.backend.core.logging import get_logger

logger = get_logger(__name__)


@scraper_registry.register
class KontaktScraper(BaseScraper):
    store_slug = "kontakt"
    store_name = "Kontakt Home"
    base_url = "https://kontakt.az"

    GRAPHQL_QUERY = """
    {
        products(search: "%s", pageSize: %d) {
            items {
                name
                url_key
                price_range {
                    minimum_price {
                        final_price {
                            value
                            currency
                        }
                    }
                }
                small_image {
                    url
                }
            }
            total_count
        }
    }
    """

    async def search(self, query: str, max_results: int = 10) -> list[ScrapedProduct]:
        return await self._search_graphql(query, max_results)

    async def _search_graphql(self, query: str, max_results: int) -> list[ScrapedProduct]:
        client = await self._get_client()
        safe_query = query.replace('"', '\\"')
        graphql_query = self.GRAPHQL_QUERY % (safe_query, max_results)

        response = await client.post(
            f"{self.base_url}/graphql",
            json={"query": graphql_query},
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Origin": self.base_url,
                "Referer": f"{self.base_url}/",
                "Sec-CH-UA": '"Google Chrome";v="131", "Chromium";v="131"',
                "Sec-CH-UA-Mobile": "?0",
                "Sec-CH-UA-Platform": '"Windows"',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
            },
        )
        response.raise_for_status()
        data = response.json()

        products = []
        items = data.get("data", {}).get("products", {}).get("items", [])
        for item in items[:max_results]:
            name = item.get("name", "")
            url_key = item.get("url_key", "")
            price_data = (
                item.get("price_range", {})
                .get("minimum_price", {})
                .get("final_price", {})
            )
            price_val = price_data.get("value", 0)
            image_data = item.get("small_image", {})
            image_url = image_data.get("url") if image_data else None

            try:
                price = Decimal(str(price_val)).quantize(Decimal("0.01"))
            except Exception:
                continue

            if price <= 0:
                continue

            products.append(ScrapedProduct(
                product_name=name,
                price=price,
                product_url=f"{self.base_url}/{url_key}.html",
                store_slug=self.store_slug,
                store_name=self.store_name,
                image_url=image_url,
            ))

        return products
