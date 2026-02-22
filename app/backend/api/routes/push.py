from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.api.dependencies import get_db
from app.backend.core.config import settings
from app.backend.models.push_subscription import PushSubscription
from app.backend.schemas.push import (
    PushSubscribeRequest,
    PushSubscriptionResponse,
    PushUnsubscribeRequest,
    VapidKeyResponse,
)

router = APIRouter(prefix="/push")


@router.get("/vapid-key", response_model=VapidKeyResponse)
async def get_vapid_key():
    if not settings.VAPID_PUBLIC_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Push notifications not configured",
        )
    return VapidKeyResponse(public_key=settings.VAPID_PUBLIC_KEY)


@router.post(
    "/subscribe",
    response_model=PushSubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def subscribe(data: PushSubscribeRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PushSubscription).where(PushSubscription.endpoint == data.endpoint)
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.p256dh = data.keys.p256dh
        existing.auth = data.keys.auth
        existing.is_active = True
        if data.user_id is not None:
            existing.user_id = data.user_id
        await db.commit()
        await db.refresh(existing)
        return existing

    sub = PushSubscription(
        endpoint=data.endpoint,
        p256dh=data.keys.p256dh,
        auth=data.keys.auth,
        user_id=data.user_id,
        is_active=True,
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return sub


@router.post("/unsubscribe", status_code=status.HTTP_200_OK)
async def unsubscribe(
    data: PushUnsubscribeRequest, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(PushSubscription).where(PushSubscription.endpoint == data.endpoint)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )
    sub.is_active = False
    await db.commit()
    return {"status": "unsubscribed"}
