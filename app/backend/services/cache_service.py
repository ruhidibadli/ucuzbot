"""Redis-backed caching for search results and scraper health tracking."""

import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal

import redis.asyncio as redis

from app.backend.core.config import settings
from app.backend.core.logging import get_logger

logger = get_logger(__name__)

_redis: redis.Redis | None = None


async def _get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


def _cache_key(query: str, store_slugs: list[str] | None) -> str:
    normalized = query.lower().strip()
    slugs_str = ",".join(sorted(store_slugs)) if store_slugs else "all"
    raw = f"{normalized}|{slugs_str}"
    digest = hashlib.md5(raw.encode()).hexdigest()
    return f"search:{digest}"


async def get_cached_search(
    query: str, store_slugs: list[str] | None = None
) -> list[dict] | None:
    try:
        r = await _get_redis()
        key = _cache_key(query, store_slugs)
        data = await r.get(key)
        if data is None:
            return None
        return json.loads(data)
    except Exception as e:
        logger.warning("cache_get_error", error=str(e))
        return None


async def set_cached_search(
    query: str,
    store_slugs: list[str] | None,
    products: list,
    ttl: int | None = None,
) -> None:
    try:
        r = await _get_redis()
        key = _cache_key(query, store_slugs)
        ttl = ttl or settings.SEARCH_CACHE_TTL
        serialized = [
            {
                "product_name": p.product_name,
                "price": str(p.price),
                "product_url": p.product_url,
                "store_slug": p.store_slug,
                "store_name": p.store_name,
                "image_url": p.image_url,
                "in_stock": p.in_stock,
            }
            for p in products
        ]
        await r.set(key, json.dumps(serialized), ex=ttl)
    except Exception as e:
        logger.warning("cache_set_error", error=str(e))


async def track_scraper_health(
    slug: str, success: bool, response_ms: int = 0
) -> None:
    try:
        r = await _get_redis()
        key = f"scraper_health:{slug}"
        now = datetime.now(timezone.utc).isoformat()
        if success:
            await r.hincrby(key, "success_count", 1)
            await r.hset(key, "last_success_at", now)
            await r.hset(key, "last_response_ms", str(response_ms))
        else:
            await r.hincrby(key, "failure_count", 1)
            await r.hset(key, "last_failure_at", now)
    except Exception as e:
        logger.warning("scraper_health_track_error", error=str(e))


async def get_scraper_health() -> dict:
    try:
        r = await _get_redis()
        keys = []
        async for key in r.scan_iter(match="scraper_health:*"):
            keys.append(key)

        result = {}
        for key in keys:
            slug = key.split(":", 1)[1]
            data = await r.hgetall(key)
            result[slug] = {
                "success_count": int(data.get("success_count", 0)),
                "failure_count": int(data.get("failure_count", 0)),
                "last_success_at": data.get("last_success_at"),
                "last_failure_at": data.get("last_failure_at"),
                "last_response_ms": int(data.get("last_response_ms", 0)),
            }
        return result
    except Exception as e:
        logger.warning("scraper_health_get_error", error=str(e))
        return {}
