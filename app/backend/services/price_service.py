from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.core.logging import get_logger
from app.backend.models.alert import Alert
from app.backend.models.price_record import PriceRecord
from app.backend.scrapers.base import ScrapedProduct

logger = get_logger(__name__)


async def record_prices(
    session: AsyncSession,
    alert: Alert,
    products: list[ScrapedProduct],
) -> PriceRecord | None:
    if not products:
        return None

    lowest: ScrapedProduct | None = None
    for product in products:
        record = PriceRecord(
            alert_id=alert.id,
            store_slug=product.store_slug,
            product_name=product.product_name,
            price=product.price,
            product_url=product.product_url,
        )
        session.add(record)
        if lowest is None or product.price < lowest.price:
            lowest = product

    now = datetime.now(timezone.utc)
    alert.last_checked_at = now

    if lowest:
        alert.lowest_price_found = lowest.price
        alert.lowest_price_store = lowest.store_slug
        alert.lowest_price_url = lowest.product_url

    await session.flush()

    if lowest:
        result = await session.execute(
            select(PriceRecord)
            .where(PriceRecord.alert_id == alert.id)
            .order_by(PriceRecord.scraped_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    return None


def check_price_trigger(alert: Alert, lowest_price: Decimal) -> bool:
    return lowest_price <= alert.target_price


async def mark_alert_triggered(session: AsyncSession, alert: Alert) -> None:
    alert.is_triggered = True
    alert.triggered_at = datetime.now(timezone.utc)
    logger.info("alert_triggered", alert_id=alert.id, price=str(alert.lowest_price_found))


async def get_price_history(session: AsyncSession, alert_id: int) -> list[PriceRecord]:
    result = await session.execute(
        select(PriceRecord)
        .where(PriceRecord.alert_id == alert_id)
        .order_by(PriceRecord.scraped_at.desc())
        .limit(100)
    )
    return list(result.scalars().all())


async def cleanup_old_records(session: AsyncSession, days: int = 90) -> int:
    from datetime import timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    result = await session.execute(
        delete(PriceRecord).where(PriceRecord.scraped_at < cutoff)
    )
    count = result.rowcount
    logger.info("cleanup_old_records", deleted=count, older_than_days=days)
    return count
