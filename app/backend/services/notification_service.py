import json
from decimal import Decimal

from app.backend.core.config import settings
from app.backend.core.logging import get_logger
from app.backend.models.alert import Alert
from app.backend.bot.keyboards import price_drop_keyboard
from app.backend.models.push_subscription import PushSubscription

logger = get_logger(__name__)

from aiogram import Bot

PRICE_DROP_TEMPLATE = """\U0001f514 Q\u0130YM\u018fT D\u00dc\u015eD\u00dc! / PRICE DROP!

\U0001f4f1 {product_name}
\U0001f4b0 {price} \u20bc (h\u0259d\u0259f: {target_price} \u20bc)
\U0001f3ea {store_name}
\U0001f517 {product_url}"""


async def send_price_alert(
    telegram_id: int,
    alert: Alert,
    product_name: str,
    price: Decimal,
    store_name: str,
    product_url: str,
) -> bool:
    try:
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        message = PRICE_DROP_TEMPLATE.format(
            product_name=product_name or alert.search_query,
            price=f"{price:,.2f}",
            target_price=f"{alert.target_price:,.2f}",
            store_name=store_name,
            product_url=product_url,
        )
        await bot.send_message(
            chat_id=telegram_id,
            text=message,
            reply_markup=price_drop_keyboard(),
        )
        await bot.session.close()
        logger.info(
            "notification_sent",
            telegram_id=telegram_id,
            alert_id=alert.id,
            price=str(price),
        )
        return True
    except Exception as e:
        logger.error(
            "notification_failed",
            telegram_id=telegram_id,
            alert_id=alert.id,
            error=str(e),
        )
        return False


async def send_push_alert(
    subscription: PushSubscription,
    alert: Alert,
    product_name: str,
    price: Decimal,
    store_name: str,
    product_url: str,
) -> bool:
    if not settings.VAPID_PRIVATE_KEY:
        logger.warning("push_skipped_no_vapid_key", alert_id=alert.id)
        return False

    try:
        from pywebpush import webpush, WebPushException
    except ImportError:
        logger.error("pywebpush_not_installed", alert_id=alert.id)
        return False

    try:
        payload = json.dumps({
            "title": "QİYMƏT DÜŞDÜ! / PRICE DROP!",
            "body": (
                f"{product_name or alert.search_query}\n"
                f"{price:,.2f} ₼ (hədəf: {alert.target_price:,.2f} ₼)\n"
                f"{store_name}"
            ),
            "url": product_url,
            "icon": "/icon-192.png",
        })

        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {
                    "p256dh": subscription.p256dh,
                    "auth": subscription.auth,
                },
            },
            data=payload,
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": settings.VAPID_CLAIMS_EMAIL},
        )

        logger.info(
            "push_notification_sent",
            alert_id=alert.id,
            endpoint=subscription.endpoint[:50],
            price=str(price),
        )
        return True
    except WebPushException as e:
        logger.error(
            "push_notification_failed",
            alert_id=alert.id,
            endpoint=subscription.endpoint[:50],
            error=str(e),
        )
        return False
    except Exception as e:
        logger.error(
            "push_notification_error",
            alert_id=alert.id,
            error=str(e),
        )
        return False


async def send_push_alerts_for_alert(
    alert: Alert,
    product_name: str,
    price: Decimal,
    store_name: str,
    product_url: str,
    session=None,
) -> int:
    """Send push notifications for an alert.
    Sends to: the alert's direct push subscription + all user's active subscriptions.
    If session is provided, uses it; otherwise creates one from the module-level factory."""
    from sqlalchemy import select, or_

    conditions = []
    if alert.user_id is not None:
        conditions.append(PushSubscription.user_id == alert.user_id)
    if alert.push_subscription_id is not None:
        conditions.append(PushSubscription.id == alert.push_subscription_id)

    if not conditions:
        return 0

    async def _query(s):
        result = await s.execute(
            select(PushSubscription).where(
                or_(*conditions),
                PushSubscription.is_active == True,  # noqa: E712
            )
        )
        return result.scalars().all()

    if session is not None:
        subscriptions = await _query(session)
    else:
        from app.backend.db.base import async_session_factory
        async with async_session_factory() as s:
            subscriptions = await _query(s)

    # Deduplicate by endpoint
    seen_endpoints: set[str] = set()
    unique_subs = []
    for sub in subscriptions:
        if sub.endpoint not in seen_endpoints:
            seen_endpoints.add(sub.endpoint)
            unique_subs.append(sub)

    sent = 0
    for sub in unique_subs:
        if await send_push_alert(sub, alert, product_name, price, store_name, product_url):
            sent += 1
    return sent
