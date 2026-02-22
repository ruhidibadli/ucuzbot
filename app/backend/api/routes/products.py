from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.api.dependencies import get_db
from app.backend.schemas.product import PriceHistoryResponse, PriceRecordResponse
from app.backend.services.price_service import get_price_history
from app.shared.constants import STORE_CONFIGS

router = APIRouter()


@router.get("/prices/{alert_id}", response_model=PriceHistoryResponse)
async def price_history(alert_id: int, db: AsyncSession = Depends(get_db)):
    records = await get_price_history(db, alert_id)
    return PriceHistoryResponse(
        alert_id=alert_id,
        records=[PriceRecordResponse.model_validate(r) for r in records],
    )


@router.get("/stores")
async def list_stores():
    return [
        {
            "slug": slug,
            "name": config["name"],
            "base_url": config["base_url"],
        }
        for slug, config in STORE_CONFIGS.items()
    ]
