from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from app.backend.scrapers.base import BaseScraper, ScrapedProduct
from app.backend.scrapers.registry import scraper_registry
from app.backend.core.logging import get_logger

logger = get_logger(__name__)


@scraper_registry.register
class IrshadScraper(BaseScraper):
    store_slug = "irshad"
    store_name = "Irshad"
    base_url = "https://irshad.az"

    async def search(self, query: str, max_results: int = 10) -> list[ScrapedProduct]:
        # Irshad loads products via AJAX from /az/products/list?q=...
        # This endpoint returns HTML with product cards in #productGridItems
        url = f"{self.base_url}/az/products/list?q={quote_plus(query)}"
        html = await self._get_page(url)
        soup = BeautifulSoup(html, "lxml")

        grid = soup.select_one("#productGridItems")
        if not grid:
            logger.warning("irshad_no_product_grid")
            return []

        products = []
        items = grid.select(".product")
        for item in items[:max_results]:
            name_el = item.select_one("a.product__name")
            if not name_el:
                continue

            name = name_el.get_text(strip=True)
            href = name_el.get("href", "")
            product_url = href if href.startswith("http") else f"{self.base_url}{href}"

            # Price: prefer .new-price (discounted), fall back to .old-price
            price_el = item.select_one(".new-price")
            if not price_el:
                price_el = item.select_one(".old-price")
            if not price_el:
                price_el = item.select_one(".product__price__current")

            if not price_el:
                continue

            try:
                price = self._parse_price(price_el.get_text(strip=True))
            except ValueError:
                continue

            img_el = item.select_one(".product__img img")
            image_url = None
            if img_el:
                image_url = img_el.get("src") or img_el.get("data-src")

            products.append(ScrapedProduct(
                product_name=name,
                price=price,
                product_url=product_url,
                store_slug=self.store_slug,
                store_name=self.store_name,
                image_url=image_url,
            ))

        return products
