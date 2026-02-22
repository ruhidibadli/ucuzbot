from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class AlertCreate(BaseModel):
    telegram_id: int | None = None
    search_query: str = Field(max_length=500)
    target_price: Decimal = Field(gt=0, decimal_places=2)
    store_slugs: list[str]
    push_endpoint: str | None = None


class AlertResponse(BaseModel):
    id: int
    search_query: str
    target_price: Decimal
    store_slugs: list[str]
    is_active: bool
    is_triggered: bool
    triggered_at: datetime | None
    last_checked_at: datetime | None
    lowest_price_found: Decimal | None
    lowest_price_store: str | None
    lowest_price_url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
