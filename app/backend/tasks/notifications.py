"""Celery tasks for retrying failed notifications."""

import asyncio
from decimal import Decimal

from app.backend.core.logging import get_logger
from app.backend.tasks.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(
    bind=True,
    name="app.backend.tasks.notifications.retry_send_telegram_alert",
    max_retries=3,
    default_retry_delay=60,
)
def retry_send_telegram_alert(self, telegram_id, alert_data, product_data):
    async def _send():
        from app.backend.services.notification_service import send_price_alert
        from types import SimpleNamespace

        alert = SimpleNamespace(**alert_data)
        alert.target_price = Decimal(alert_data["target_price"])

        success = await send_price_alert(
            telegram_id=telegram_id,
            alert=alert,
            product_name=product_data["product_name"],
            price=Decimal(product_data["price"]),
            store_name=product_data["store_name"],
            product_url=product_data["product_url"],
        )
        return success

    try:
        success = asyncio.run(_send())
        if not success:
            raise Exception("Telegram notification send returned False")
        logger.info("retry_telegram_success", telegram_id=telegram_id, attempt=self.request.retries + 1)
    except Exception as exc:
        countdown = 60 * (2 ** self.request.retries)
        logger.warning(
            "retry_telegram_failed",
            telegram_id=telegram_id,
            attempt=self.request.retries + 1,
            next_retry_seconds=countdown,
        )
        raise self.retry(exc=exc, countdown=countdown)


@celery_app.task(
    bind=True,
    name="app.backend.tasks.notifications.retry_send_push_alert",
    max_retries=3,
    default_retry_delay=60,
)
def retry_send_push_alert(self, subscription_data, alert_data, product_data):
    async def _send():
        from app.backend.services.notification_service import send_push_alert
        from app.backend.models.push_subscription import PushSubscription
        from types import SimpleNamespace

        sub = SimpleNamespace(**subscription_data)
        alert = SimpleNamespace(**alert_data)
        alert.target_price = Decimal(alert_data["target_price"])

        success = await send_push_alert(
            subscription=sub,
            alert=alert,
            product_name=product_data["product_name"],
            price=Decimal(product_data["price"]),
            store_name=product_data["store_name"],
            product_url=product_data["product_url"],
        )
        return success

    try:
        success = asyncio.run(_send())
        if not success:
            raise Exception("Push notification send returned False")
        logger.info("retry_push_success", attempt=self.request.retries + 1)
    except Exception as exc:
        countdown = 60 * (2 ** self.request.retries)
        logger.warning(
            "retry_push_failed",
            attempt=self.request.retries + 1,
            next_retry_seconds=countdown,
        )
        raise self.retry(exc=exc, countdown=countdown)
