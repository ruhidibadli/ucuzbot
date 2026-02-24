from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from app.backend.scrapers.base import BaseScraper, ScrapedProduct
from app.backend.scrapers.registry import scraper_registry
from app.backend.core.config import settings
from app.backend.core.logging import get_logger
from app.shared.constants import DEFAULT_HEADERS

logger = get_logger(__name__)


@scraper_registry.register
class MaxiScraper(BaseScraper):
    store_slug = "maxi"
    store_name = "Maxi.az"
    base_url = "https://maxi.az"

    @retry(stop=stop_after_attempt(1), reraise=True)
    async def _get_page(self, url: str) -> str:
        """Override base _get_page with single attempt and shorter timeout."""
        client = await self._get_client()
        response = await client.get(url, timeout=10)
        response.raise_for_status()
        return response.text

    async def search(self, query: str, max_results: int = 10) -> list[ScrapedProduct]:
        url = f"{self.base_url}/axtaris?q={quote_plus(query)}"
        try:
            html = await self._get_page(url)
        except Exception as e:
            logger.warning("maxi_site_unavailable", error=str(e))
            return []

        soup = BeautifulSoup(html, "lxml")

        # Check for proxy/maintenance page
        if "proxy" in soup.get_text().lower() or len(soup.get_text(strip=True)) < 100:
            logger.warning("maxi_site_maintenance")
            return []

        products = []
        items = soup.select(
            ".product-card, .product-item, .catalog-item, "
            ".product-list__item, .products .item"
        )
        for item in items[:max_results]:
            name_el = item.select_one(
                ".product-card__name, .product-name, .product-title, "
                "h3 a, h4 a, .product-card__title"
            )
            price_el = item.select_one(
                ".product-card__price, .product-price, .price, "
                ".current-price"
            )
            link_el = item.select_one("a[href]")
            img_el = item.select_one("img[src], img[data-src]")

            if not name_el or not price_el:
                continue

            name = name_el.get_text(strip=True)
            try:
                price = self._parse_price(price_el.get_text(strip=True))
            except ValueError:
                continue

            href = link_el["href"] if link_el else ""
            product_url = href if href.startswith("http") else f"{self.base_url}{href}"
            image_url = img_el.get("src") or img_el.get("data-src") if img_el else None

            products.append(ScrapedProduct(
                product_name=name,
                price=price,
                product_url=product_url,
                store_slug=self.store_slug,
                store_name=self.store_name,
                image_url=image_url,
            ))
            await self._delay()

        return products
