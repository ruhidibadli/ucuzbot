import asyncio
from datetime import datetime, timezone

from app.backend.core.logging import get_logger
from app.backend.scrapers.base import ScrapedProduct
from app.backend.scrapers.registry import scraper_registry
from app.backend.services.relevance import filter_relevant
from app.shared.constants import StoreSlug

logger = get_logger(__name__)


async def search_all_stores(
    query: str,
    store_slugs: list[str] | None = None,
    max_results_per_store: int = 10,
) -> tuple[list[ScrapedProduct], list[str]]:
    all_scrapers = scraper_registry.get_all()
    if store_slugs:
        scrapers_to_use = {k: v for k, v in all_scrapers.items() if k in store_slugs}
    else:
        scrapers_to_use = all_scrapers

    tasks = []
    for slug, scraper_cls in scrapers_to_use.items():
        scraper = scraper_cls()
        tasks.append(scraper.safe_search(query, max_results_per_store))

    results_list = await asyncio.gather(*tasks, return_exceptions=True)

    all_products: list[ScrapedProduct] = []
    errors: list[str] = []

    for slug, result in zip(scrapers_to_use.keys(), results_list):
        if isinstance(result, Exception):
            errors.append(f"{slug}: {result}")
            logger.error("search_store_error", store=slug, error=str(result))
        elif isinstance(result, list):
            all_products.extend(result)
        else:
            errors.append(f"{slug}: unexpected result type")

    all_products.sort(key=lambda p: p.price)
    all_products = filter_relevant(all_products, query)
    return all_products, errors


async def search_stores_for_alert(
    query: str,
    store_slugs: list[str],
    max_results_per_store: int = 5,
) -> list[ScrapedProduct]:
    products, _ = await search_all_stores(query, store_slugs, max_results_per_store)
    return products
