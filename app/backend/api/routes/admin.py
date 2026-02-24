from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.api.dependencies import get_admin_user, get_db
from app.backend.models.alert import Alert
from app.backend.models.bot_activity import BotActivity
from app.backend.models.user import User
from app.backend.schemas.admin import (
    AdminAlertListItem,
    AdminAlertListResponse,
    AdminBotActivityItem,
    AdminBotActivityResponse,
    AdminStatsResponse,
    AdminUserListItem,
    AdminUserListResponse,
)

router = APIRouter()


@router.get("/admin/stats", response_model=AdminStatsResponse)
async def admin_stats(
    _admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    total_users = (await db.execute(select(func.count(User.id)))).scalar_one()
    total_alerts = (await db.execute(select(func.count(Alert.id)))).scalar_one()

    active_alerts = (await db.execute(
        select(func.count(Alert.id)).where(Alert.is_active == True, Alert.is_triggered == False)  # noqa: E712
    )).scalar_one()

    triggered_alerts = (await db.execute(
        select(func.count(Alert.id)).where(Alert.is_triggered == True)  # noqa: E712
    )).scalar_one()

    inactive_alerts = (await db.execute(
        select(func.count(Alert.id)).where(Alert.is_active == False)  # noqa: E712
    )).scalar_one()

    # Alerts by store: unnest the store_slugs array and count
    unnested = select(func.unnest(Alert.store_slugs).label("slug")).subquery()
    store_rows = (await db.execute(
        select(unnested.c.slug, func.count()).group_by(unnested.c.slug)
    )).all()
    alerts_by_store = {row[0]: row[1] for row in store_rows}

    now = datetime.now(timezone.utc)
    recent_24h = (await db.execute(
        select(func.count(Alert.id)).where(
            Alert.is_triggered == True,  # noqa: E712
            Alert.triggered_at >= now - timedelta(hours=24),
        )
    )).scalar_one()

    recent_7d = (await db.execute(
        select(func.count(Alert.id)).where(
            Alert.is_triggered == True,  # noqa: E712
            Alert.triggered_at >= now - timedelta(days=7),
        )
    )).scalar_one()

    return AdminStatsResponse(
        total_users=total_users,
        total_alerts=total_alerts,
        active_alerts=active_alerts,
        triggered_alerts=triggered_alerts,
        inactive_alerts=inactive_alerts,
        alerts_by_store=alerts_by_store,
        recent_triggered_count_24h=recent_24h,
        recent_triggered_count_7d=recent_7d,
    )


@router.get("/admin/users", response_model=AdminUserListResponse)
async def admin_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query("", max_length=255),
    _admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    base = select(User)
    count_base = select(func.count(User.id))

    if search.strip():
        pattern = f"%{search.strip().lower()}%"
        filter_cond = (func.lower(User.email).like(pattern)) | (func.lower(User.first_name).like(pattern))
        base = base.where(filter_cond)
        count_base = count_base.where(filter_cond)

    total = (await db.execute(count_base)).scalar_one()

    offset = (page - 1) * page_size
    users = (await db.execute(
        base.order_by(User.created_at.desc()).offset(offset).limit(page_size)
    )).scalars().all()

    # Get alert counts per user in bulk
    user_ids = [u.id for u in users]
    alert_counts_q = (
        select(
            Alert.user_id,
            func.count(Alert.id).label("alert_count"),
            func.count(case((Alert.is_active == True, 1))).label("active_count"),  # noqa: E712
            func.count(case((Alert.is_triggered == True, 1))).label("triggered_count"),  # noqa: E712
        )
        .where(Alert.user_id.in_(user_ids))
        .group_by(Alert.user_id)
    )
    alert_rows = (await db.execute(alert_counts_q)).all()
    counts_map = {r[0]: (r[1], r[2], r[3]) for r in alert_rows}

    items = []
    for u in users:
        ac, aac, atc = counts_map.get(u.id, (0, 0, 0))
        items.append(AdminUserListItem(
            id=u.id,
            email=u.email,
            telegram_id=u.telegram_id,
            first_name=u.first_name,
            subscription_tier=u.subscription_tier,
            alert_count=ac,
            active_alert_count=aac,
            triggered_alert_count=atc,
            is_active=u.is_active,
            created_at=u.created_at,
        ))

    return AdminUserListResponse(users=items, total=total, page=page, page_size=page_size)


@router.get("/admin/alerts", response_model=AdminAlertListResponse)
async def admin_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str = Query("all", pattern="^(all|active|triggered|inactive)$"),
    store_slug: str = Query("", max_length=100),
    _admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    base = select(Alert).outerjoin(User, Alert.user_id == User.id)
    count_base = select(func.count(Alert.id))

    if status_filter == "active":
        cond = (Alert.is_active == True) & (Alert.is_triggered == False)  # noqa: E712
        base = base.where(cond)
        count_base = count_base.where(cond)
    elif status_filter == "triggered":
        cond = Alert.is_triggered == True  # noqa: E712
        base = base.where(cond)
        count_base = count_base.where(cond)
    elif status_filter == "inactive":
        cond = Alert.is_active == False  # noqa: E712
        base = base.where(cond)
        count_base = count_base.where(cond)

    if store_slug.strip():
        slug_cond = Alert.store_slugs.any(store_slug.strip())
        base = base.where(slug_cond)
        count_base = count_base.where(slug_cond)

    total = (await db.execute(count_base)).scalar_one()

    offset = (page - 1) * page_size
    base = base.add_columns(User.email, User.first_name)
    rows = (await db.execute(
        base.order_by(Alert.created_at.desc()).offset(offset).limit(page_size)
    )).all()

    items = []
    for alert, user_email, user_first_name in rows:
        items.append(AdminAlertListItem(
            id=alert.id,
            user_id=alert.user_id,
            user_email=user_email,
            user_first_name=user_first_name,
            search_query=alert.search_query,
            target_price=alert.target_price,
            store_slugs=alert.store_slugs,
            is_active=alert.is_active,
            is_triggered=alert.is_triggered,
            triggered_at=alert.triggered_at,
            last_checked_at=alert.last_checked_at,
            lowest_price_found=alert.lowest_price_found,
            lowest_price_store=alert.lowest_price_store,
            lowest_price_url=alert.lowest_price_url,
            created_at=alert.created_at,
        ))

    return AdminAlertListResponse(alerts=items, total=total, page=page, page_size=page_size)


@router.get("/admin/bot-activity", response_model=AdminBotActivityResponse)
async def admin_bot_activity(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    action_filter: str = Query("all", pattern="^(all|search|alert_create|alert_delete|alert_triggered)$"),
    _admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    base = select(BotActivity).outerjoin(User, BotActivity.user_id == User.id)
    count_base = select(func.count(BotActivity.id))

    if action_filter != "all":
        base = base.where(BotActivity.action == action_filter)
        count_base = count_base.where(BotActivity.action == action_filter)

    total = (await db.execute(count_base)).scalar_one()

    offset = (page - 1) * page_size
    base = base.add_columns(User.email, User.first_name)
    rows = (await db.execute(
        base.order_by(BotActivity.created_at.desc()).offset(offset).limit(page_size)
    )).all()

    items = []
    for activity, user_email, user_first_name in rows:
        items.append(AdminBotActivityItem(
            id=activity.id,
            user_id=activity.user_id,
            telegram_id=activity.telegram_id,
            user_email=user_email,
            user_first_name=user_first_name,
            action=activity.action,
            detail=activity.detail,
            created_at=activity.created_at,
        ))

    return AdminBotActivityResponse(activities=items, total=total, page=page, page_size=page_size)
