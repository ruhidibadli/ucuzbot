import asyncio

from app.backend.core.logging import get_logger
from app.backend.db.base import async_session_factory, engine
from app.backend.models.alert import Alert
from app.backend.services.alert_service import get_all_active_alerts
from app.backend.services.notification_service import send_price_alert, send_push_alerts_for_alert
from app.backend.services.price_service import check_price_trigger, mark_alert_triggered, record_prices
from app.backend.services.search_service import search_stores_for_alert
from app.backend.tasks.celery_app import celery_app
from app.shared.constants import STORE_CONFIGS

logger = get_logger(__name__)


async def _check_single_alert(alert_id: int) -> None:
    await engine.dispose()
    async with async_session_factory() as session:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        result = await session.execute(
            select(Alert).options(selectinload(Alert.user)).where(Alert.id == alert_id)
        )
        alert = result.scalar_one_or_none()
        if not alert or not alert.is_active or alert.is_triggered:
            return

        from datetime import datetime, timezone

        products = await search_stores_for_alert(alert.search_query, alert.store_slugs)
        alert.last_checked_at = datetime.now(timezone.utc)

        if not products:
            logger.info("no_products_found", alert_id=alert.id)
            await session.commit()
            return

        await record_prices(session, alert, products)

        lowest = products[0]  # Already sorted by price
        if check_price_trigger(alert, lowest.price):
            await mark_alert_triggered(session, alert)
            store_config = STORE_CONFIGS.get(lowest.store_slug, {})
            store_name = store_config.get("name", lowest.store_slug)

            if alert.user and alert.user.telegram_id:
                await send_price_alert(
                    telegram_id=alert.user.telegram_id,
                    alert=alert,
                    product_name=lowest.product_name,
                    price=lowest.price,
                    store_name=store_name,
                    product_url=lowest.product_url,
                )

            # Send browser push notifications
            await send_push_alerts_for_alert(
                alert=alert,
                product_name=lowest.product_name,
                price=lowest.price,
                store_name=store_name,
                product_url=lowest.product_url,
            )

        await session.commit()


async def _check_all_alerts() -> None:
    await engine.dispose()
    async with async_session_factory() as session:
        alerts = await get_all_active_alerts(session)
        alert_ids = [a.id for a in alerts]

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
