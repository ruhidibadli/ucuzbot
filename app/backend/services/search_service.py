import asyncio
import time
from datetime import datetime, timezone
from decimal import Decimal

from app.backend.core.logging import get_logger
from app.backend.scrapers.base import ScrapedProduct
from app.backend.scrapers.registry import scraper_registry
from app.backend.services.cache_service import (
    get_cached_search,
    set_cached_search,
    track_scraper_health,
)
from app.backend.services.relevance import filter_relevant
from app.shared.constants import StoreSlug

logger = get_logger(__name__)


async def _scrape_with_timeout(
    scraper, query: str, max_results: int, timeout: float = 30.0
) -> list[ScrapedProduct]:
    try:
        return await asyncio.wait_for(
            scraper.safe_search(query, max_results), timeout=timeout
        )
    except asyncio.TimeoutError:
        try:
            await scraper.close()
        except Exception:
            pass
        raise


def _deserialize_products(cached: list[dict]) -> list[ScrapedProduct]:
    return [
        ScrapedProduct(
            product_name=item["product_name"],
            price=Decimal(item["price"]),
            product_url=item["product_url"],
            store_slug=item["store_slug"],
            store_name=item["store_name"],
            image_url=item.get("image_url"),
            in_stock=item.get("in_stock", True),
        )
        for item in cached
    ]


async def search_all_stores(
    query: str,
    store_slugs: list[str] | None = None,
    max_results_per_store: int = 10,
    product_category: str | None = None,
) -> tuple[list[ScrapedProduct], list[str]]:
    # Check cache first
    cached = await get_cached_search(query, store_slugs)
    if cached is not None:
        logger.info("search_cache_hit", query=query)
        all_products = _deserialize_products(cached)
        all_products.sort(key=lambda p: p.price)
        all_products = filter_relevant(all_products, query, product_category=product_category)
        return all_products, []

    all_scrapers = scraper_registry.get_all()
    if store_slugs:
        scrapers_to_use = {k: v for k, v in all_scrapers.items() if k in store_slugs}
    else:
        scrapers_to_use = all_scrapers

    tasks = []
    slugs_order = list(scrapers_to_use.keys())
    for slug, scraper_cls in scrapers_to_use.items():
        scraper = scraper_cls()
        tasks.append(_scrape_with_timeout(scraper, query, max_results_per_store))

    start_times = {slug: time.monotonic() for slug in slugs_order}
    results_list = await asyncio.gather(*tasks, return_exceptions=True)

    all_products: list[ScrapedProduct] = []
    errors: list[str] = []

    for slug, result in zip(slugs_order, results_list):
        elapsed_ms = int((time.monotonic() - start_times[slug]) * 1000)

        if isinstance(result, asyncio.TimeoutError):
            errors.append(f"{slug}: timed out")
            logger.warning("search_store_timeout", store=slug)
            await track_scraper_health(slug, success=False, response_ms=elapsed_ms)
        elif isinstance(result, Exception):
            errors.append(f"{slug}: {result}")
            logger.error("search_store_error", store=slug, error=str(result))
            await track_scraper_health(slug, success=False, response_ms=elapsed_ms)
        elif isinstance(result, list):
            all_products.extend(result)
            await track_scraper_health(slug, success=True, response_ms=elapsed_ms)
        else:
            errors.append(f"{slug}: unexpected result type")
            await track_scraper_health(slug, success=False, response_ms=elapsed_ms)

    # Cache raw products before relevance filtering
    if all_products:
        await set_cached_search(query, store_slugs, all_products)

    all_products.sort(key=lambda p: p.price)
    all_products = filter_relevant(all_products, query, product_category=product_category)
    return all_products, errors


async def search_stores_for_alert(
    query: str,
    store_slugs: list[str],
    max_results_per_store: int = 5,
    product_category: str | None = None,
) -> list[ScrapedProduct]:
    products, _ = await search_all_stores(query, store_slugs, max_results_per_store, product_category=product_category)
    return products
