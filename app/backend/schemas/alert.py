from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator

from app.shared.constants import StoreSlug

VALID_STORE_SLUGS = {s.value for s in StoreSlug}


class AlertCreate(BaseModel):
    telegram_id: int | None = None
    search_query: str = Field(max_length=500)
    target_price: Decimal = Field(gt=0, decimal_places=2)
    store_slugs: list[str] = Field(min_length=1)
    product_category: str | None = None
    push_endpoint: str | None = None

    @field_validator("store_slugs")
    @classmethod
    def validate_store_slugs(cls, v: list[str]) -> list[str]:
        invalid = [s for s in v if s not in VALID_STORE_SLUGS]
        if invalid:
            raise ValueError(f"Invalid store slugs: {', '.join(invalid)}")
        return v


class AlertResponse(BaseModel):
    id: int
    search_query: str
    target_price: Decimal
    store_slugs: list[str]
    product_category: str | None = None
    is_active: bool
    is_triggered: bool
    triggered_at: datetime | None
    last_checked_at: datetime | None
    lowest_price_found: Decimal | None
    lowest_price_store: str | None
    lowest_price_url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
