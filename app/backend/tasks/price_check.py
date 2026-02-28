import asyncio
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

from app.backend.core.config import settings
from app.backend.core.logging import get_logger
from app.backend.models.alert import Alert
from app.backend.models.bot_activity import log_bot_activity
from app.backend.services.alert_service import get_all_active_alerts
from app.backend.services.notification_service import send_price_alert, send_push_alerts_for_alert
from app.backend.services.price_service import check_price_trigger, mark_alert_triggered, record_prices
from app.backend.services.search_service import search_stores_for_alert
from app.backend.tasks.celery_app import celery_app
from app.shared.constants import STORE_CONFIGS

logger = get_logger(__name__)


def _make_session_factory() -> tuple:
    """Create a fresh engine + session factory for each task invocation.
    This avoids stale connections across asyncio.run() calls in Celery."""
    task_engine = create_async_engine(
        settings.database_url, echo=False, pool_pre_ping=True, pool_size=2, max_overflow=0
    )
    factory = async_sessionmaker(task_engine, class_=AsyncSession, expire_on_commit=False)
    return task_engine, factory


def _is_quiet_hours(user) -> bool:
    if user is None:
        return False
    if user.quiet_hours_start is None or user.quiet_hours_end is None:
        return False
    try:
        import zoneinfo
        tz = zoneinfo.ZoneInfo("Asia/Baku")
    except Exception:
        return False
    current_hour = datetime.now(tz).hour
    start = user.quiet_hours_start
    end = user.quiet_hours_end
    if start <= end:
        return start <= current_hour < end
    else:
        # Wraps midnight, e.g. 23 -> 7
        return current_hour >= start or current_hour < end


def _make_alert_data(alert) -> dict:
    return {
        "id": alert.id,
        "search_query": alert.search_query,
        "target_price": str(alert.target_price),
    }


def _make_product_data(product, store_name: str) -> dict:
    return {
        "product_name": product.product_name,
        "price": str(product.price),
        "store_name": store_name,
        "product_url": product.product_url,
    }


async def _check_single_alert(alert_id: int) -> None:
    task_engine, session_factory = _make_session_factory()
    try:
        async with session_factory() as session:
            result = await session.execute(
                select(Alert).options(selectinload(Alert.user)).where(Alert.id == alert_id)
            )
            alert = result.scalar_one_or_none()
            if not alert or not alert.is_active or alert.is_triggered:
                return

            products = await search_stores_for_alert(
                alert.search_query, alert.store_slugs, product_category=alert.product_category
            )
            alert.last_checked_at = datetime.now(timezone.utc)

            if not products:
                logger.info("no_products_found", alert_id=alert.id)
                await session.commit()
                return

            await record_prices(session, alert, products)

            lowest = products[0]  # Already sorted by price
            if check_price_trigger(alert, lowest.price):
                # Check quiet hours — skip notification but don't mark triggered
                if _is_quiet_hours(alert.user):
                    logger.info("quiet_hours_skipped", alert_id=alert.id)
                    await session.commit()
                    return

                await mark_alert_triggered(session, alert)
                store_config = STORE_CONFIGS.get(lowest.store_slug, {})
                store_name = store_config.get("name", lowest.store_slug)

                await log_bot_activity(
                    session,
                    user_id=alert.user_id,
                    telegram_id=alert.user.telegram_id if alert.user else None,
                    action="alert_triggered",
                    detail=f"{alert.search_query} → {lowest.price} AZN at {lowest.store_slug}",
                )

                if alert.user and alert.user.telegram_id:
                    success = await send_price_alert(
                        telegram_id=alert.user.telegram_id,
                        alert=alert,
                        product_name=lowest.product_name,
                        price=lowest.price,
                        store_name=store_name,
                        product_url=lowest.product_url,
                    )
                    if not success:
                        from app.backend.tasks.notifications import retry_send_telegram_alert
                        retry_send_telegram_alert.delay(
                            alert.user.telegram_id,
                            _make_alert_data(alert),
                            _make_product_data(lowest, store_name),
                        )

                # Send browser push notifications
                await send_push_alerts_for_alert(
                    alert=alert,
                    product_name=lowest.product_name,
                    price=lowest.price,
                    store_name=store_name,
                    product_url=lowest.product_url,
                    session=session,
                )

            await session.commit()
    finally:
        await task_engine.dispose()


async def _check_all_alerts() -> None:
    task_engine, session_factory = _make_session_factory()
    try:
        async with session_factory() as session:
            alerts = await get_all_active_alerts(session)
            alert_ids = [a.id for a in alerts]
    finally:
        await task_engine.dispose()

    logger.info("price_check_started", total_alerts=len(alert_ids))

    for alert_id in alert_ids:
        try:
            await _check_single_alert(alert_id)
        except Exception as e:
            logger.error("alert_check_failed", alert_id=alert_id, error=str(e))

    logger.info("price_check_completed", total_alerts=len(alert_ids))


@celery_app.task(name="app.backend.tasks.price_check.check_all_alerts")
def check_all_alerts() -> None:
    asyncio.run(_check_all_alerts())


@celery_app.task(name="app.backend.tasks.price_check.check_single_alert")
def check_single_alert(alert_id: int) -> None:
    asyncio.run(_check_single_alert(alert_id))
