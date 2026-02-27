from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.core.exceptions import AlertNotFound, DuplicateAlert
from app.backend.core.logging import get_logger
from app.backend.models.alert import Alert
from app.backend.models.push_subscription import PushSubscription
from app.backend.models.user import User

logger = get_logger(__name__)


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None = None,
    first_name: str | None = None,
    language_code: str = "az",
) -> User:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user:
        if username:
            user.username = username
        if first_name:
            user.first_name = first_name
        return user

    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        language_code=language_code,
    )
    session.add(user)
    await session.flush()
    return user


async def create_alert(
    session: AsyncSession,
    user: User,
    search_query: str,
    target_price: Decimal,
    store_slugs: list[str],
) -> Alert:
    existing = await _find_duplicate_alert(session, user_id=user.id, search_query=search_query)
    if existing:
        raise DuplicateAlert(search_query)

    alert = Alert(
        user_id=user.id,
        search_query=search_query,
        target_price=target_price,
        store_slugs=store_slugs,
    )
    session.add(alert)
    await session.flush()
    logger.info("alert_created", alert_id=alert.id, user_id=user.id, query=search_query)
    return alert


async def create_alert_for_push(
    session: AsyncSession,
    push_sub: PushSubscription,
    search_query: str,
    target_price: Decimal,
    store_slugs: list[str],
) -> Alert:
    if push_sub.user_id:
        existing = await _find_duplicate_alert(session, user_id=push_sub.user_id, search_query=search_query)
        if existing:
            raise DuplicateAlert(search_query)
    else:
        existing = await _find_duplicate_alert_by_push(session, push_subscription_id=push_sub.id, search_query=search_query)
        if existing:
            raise DuplicateAlert(search_query)

    alert = Alert(
        user_id=push_sub.user_id,
        push_subscription_id=push_sub.id,
        search_query=search_query,
        target_price=target_price,
        store_slugs=store_slugs,
    )
    session.add(alert)
    await session.flush()
    logger.info(
        "alert_created_via_push",
        alert_id=alert.id,
        push_endpoint=push_sub.endpoint[:50],
        query=search_query,
    )
    return alert


async def get_user_alerts(session: AsyncSession, telegram_id: int) -> list[Alert]:
    result = await session.execute(
        select(Alert)
        .join(User)
        .where(User.telegram_id == telegram_id, Alert.is_active == True)  # noqa: E712
        .order_by(Alert.created_at.desc())
    )
    return list(result.scalars().all())


async def get_alerts_by_push_endpoint(session: AsyncSession, endpoint: str) -> list[Alert]:
    result = await session.execute(
        select(Alert)
        .join(PushSubscription, Alert.push_subscription_id == PushSubscription.id)
        .where(PushSubscription.endpoint == endpoint, Alert.is_active == True)  # noqa: E712
        .order_by(Alert.created_at.desc())
    )
    return list(result.scalars().all())


async def get_all_active_alerts(session: AsyncSession) -> list[Alert]:
    result = await session.execute(
        select(Alert).where(Alert.is_active == True, Alert.is_triggered == False)  # noqa: E712
    )
    return list(result.scalars().all())


async def delete_alert(session: AsyncSession, alert_id: int, telegram_id: int) -> None:
    result = await session.execute(
        select(Alert)
        .join(User)
        .where(Alert.id == alert_id, User.telegram_id == telegram_id)
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise AlertNotFound(f"Alert {alert_id} not found")
    alert.is_active = False
    logger.info("alert_deleted", alert_id=alert_id)


async def _find_duplicate_alert(
    session: AsyncSession, user_id: int, search_query: str
) -> Alert | None:
    from sqlalchemy import func

    result = await session.execute(
        select(Alert).where(
            Alert.user_id == user_id,
            Alert.is_active == True,  # noqa: E712
            func.lower(Alert.search_query) == search_query.lower(),
        )
    )
    return result.scalar_one_or_none()


async def _find_duplicate_alert_by_push(
    session: AsyncSession, push_subscription_id: int, search_query: str
) -> Alert | None:
    from sqlalchemy import func

    result = await session.execute(
        select(Alert).where(
            Alert.push_subscription_id == push_subscription_id,
            Alert.is_active == True,  # noqa: E712
            func.lower(Alert.search_query) == search_query.lower(),
        )
    )
    return result.scalar_one_or_none()
