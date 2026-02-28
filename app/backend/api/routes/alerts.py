from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.api.dependencies import get_current_user, get_db, get_optional_user
from app.backend.core.exceptions import AlertNotFound, DuplicateAlert
from app.backend.models.alert import Alert
from app.backend.models.push_subscription import PushSubscription
from app.backend.models.user import User
from app.backend.schemas.alert import AlertCreate, AlertResponse
from app.backend.services.alert_service import (
    create_alert,
    create_alert_for_push,
    delete_alert,
    get_alerts_by_push_endpoint,
    get_or_create_user,
    get_user_alerts,
)
from app.backend.tasks.price_check import check_single_alert

router = APIRouter()


# IMPORTANT: /alerts/me MUST be registered before /alerts/{telegram_id}
@router.get("/alerts/me", response_model=list[AlertResponse])
async def list_my_alerts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Alert)
        .where(Alert.user_id == user.id, Alert.is_active == True)  # noqa: E712
        .order_by(Alert.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/alerts/{telegram_id}", response_model=list[AlertResponse])
async def list_alerts(telegram_id: int, db: AsyncSession = Depends(get_db)):
    alerts = await get_user_alerts(db, telegram_id)
    return alerts


@router.post("/alerts", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_new_alert(
    data: AlertCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    # JWT-authenticated user (no push or telegram needed)
    if current_user and data.telegram_id is None and data.push_endpoint is None:
        try:
            alert = await create_alert(
                db, current_user, data.search_query, data.target_price, data.store_slugs,
                product_category=data.product_category,
            )
            await db.commit()
        except DuplicateAlert as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        try:
            check_single_alert.delay(alert.id)
        except Exception:
            pass
        return alert

    if data.telegram_id is None and data.push_endpoint is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either telegram_id or push_endpoint is required",
        )

    if data.telegram_id is not None:
        user = await get_or_create_user(db, data.telegram_id)
        try:
            alert = await create_alert(
                db, user, data.search_query, data.target_price, data.store_slugs,
                product_category=data.product_category,
            )
            await db.commit()
        except DuplicateAlert as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        try:
            check_single_alert.delay(alert.id)
        except Exception:
            pass
        return alert

    # Browser push-based alert (no Telegram)
    result = await db.execute(
        select(PushSubscription).where(
            PushSubscription.endpoint == data.push_endpoint,
            PushSubscription.is_active == True,  # noqa: E712
        )
    )
    push_sub = result.scalar_one_or_none()
    if not push_sub:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Push subscription not found. Subscribe to push notifications first.",
        )
    try:
        alert = await create_alert_for_push(
            db, push_sub, data.search_query, data.target_price, data.store_slugs,
            product_category=data.product_category,
        )
        await db.commit()
    except DuplicateAlert as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    try:
        check_single_alert.delay(alert.id)
    except Exception:
        pass
    return alert


@router.post("/alerts/by-push", response_model=list[AlertResponse])
async def list_alerts_by_push(
    data: dict, db: AsyncSession = Depends(get_db)
):
    endpoint = data.get("endpoint")
    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="endpoint is required",
        )
    alerts = await get_alerts_by_push_endpoint(db, endpoint)
    return alerts


@router.post("/alerts/{alert_id}/check")
async def check_alert_now(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    if not alert.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Alert is not active")

    # Ownership check for authenticated users
    if current_user and alert.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your alert")

    check_single_alert.delay(alert_id)
    return {"status": "checking", "alert_id": alert_id}


@router.delete("/alerts/{alert_id}")
async def remove_alert(
    alert_id: int,
    telegram_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    # JWT-authenticated delete with ownership check
    if current_user:
        result = await db.execute(select(Alert).where(Alert.id == alert_id))
        alert = result.scalar_one_or_none()
        if not alert:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
        if alert.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your alert")
        alert.is_active = False
        await db.commit()
        return {"status": "deleted"}

    if telegram_id is not None:
        try:
            await delete_alert(db, alert_id, telegram_id)
            await db.commit()
            return {"status": "deleted"}
        except AlertNotFound as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    # Push-based delete: just soft-delete by alert ID
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    alert.is_active = False
    await db.commit()
    return {"status": "deleted"}
