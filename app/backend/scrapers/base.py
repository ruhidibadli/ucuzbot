import asyncio
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.backend.core.config import settings
from app.backend.core.logging import get_logger
from app.shared.constants import DEFAULT_HEADERS

logger = get_logger(__name__)


@dataclass
class ScrapedProduct:
    product_name: str
    price: Decimal
    product_url: str
    store_slug: str
    store_name: str
    image_url: str | None = None
    in_stock: bool = True
    scraped_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class BaseScraper(ABC):
    store_slug: str
    store_name: str
    base_url: str

    def __init__(self):
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=settings.SCRAPER_TIMEOUT,
                headers={
                    "User-Agent": settings.SCRAPER_USER_AGENT,
                    **DEFAULT_HEADERS,
                },
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    @abstractmethod
    async def search(self, query: str, max_results: int = 10) -> list[ScrapedProduct]:
        ...

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=8), reraise=True)
    async def _get_page(self, url: str) -> str:
        client = await self._get_client()
        response = await client.get(url)
        response.raise_for_status()
        return response.text

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=8), reraise=True)
    async def _get_json(self, url: str, params: dict | None = None) -> dict:
        client = await self._get_client()
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def _delay(self) -> None:
        await asyncio.sleep(settings.SCRAPER_REQUEST_DELAY)

    @staticmethod
    def _parse_price(price_str: str) -> Decimal:
        if not price_str:
            raise ValueError("Empty price string")

        cleaned = price_str.strip()
        cleaned = re.sub(r"[₼AZNazn\s]", "", cleaned)
        cleaned = cleaned.strip()

        if not cleaned:
            raise ValueError(f"No numeric value in price: {price_str}")

        # Handle "1.299,00" format (dot as thousands, comma as decimal)
        if re.match(r"^\d{1,3}(\.\d{3})+(,\d{2})?$", cleaned):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        # Handle "1,299.00" format (comma as thousands, dot as decimal)
        elif re.match(r"^\d{1,3}(,\d{3})+(\.\d{2})?$", cleaned):
            cleaned = cleaned.replace(",", "")
        # Handle "1 299,00" or "1 299.00" format (space as thousands)
        elif re.match(r"^\d{1,3}(\s\d{3})+([\.,]\d{2})?$", cleaned):
            cleaned = cleaned.replace(" ", "").replace(",", ".")
        # Handle simple "1299" or "1299.99"
        elif re.match(r"^\d+(\.\d+)?$", cleaned):
            pass
        # Handle "1299,99" (comma as decimal)
        elif re.match(r"^\d+,\d+$", cleaned):
            cleaned = cleaned.replace(",", ".")
        else:
            cleaned = re.sub(r"[^\d.,]", "", cleaned)
            if "," in cleaned and "." in cleaned:
                if cleaned.rfind(",") > cleaned.rfind("."):
                    cleaned = cleaned.replace(".", "").replace(",", ".")
                else:
                    cleaned = cleaned.replace(",", "")
            elif "," in cleaned:
                cleaned = cleaned.replace(",", ".")

        try:
            return Decimal(cleaned).quantize(Decimal("0.01"))
        except InvalidOperation as e:
            raise ValueError(f"Cannot parse price: {price_str}") from e

    async def safe_search(self, query: str, max_results: int = 10) -> list[ScrapedProduct]:
        try:
            results = await self.search(query, max_results)
            logger.info("scraper_search_success", store=self.store_slug, query=query, results=len(results))
            return results
        except Exception as e:
            logger.error("scraper_search_failed", store=self.store_slug, query=query, error=str(e))
            return []
        finally:
            await self.close()
