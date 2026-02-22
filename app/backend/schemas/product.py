from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel


class PriceRecordResponse(BaseModel):
    id: int
    store_slug: str
    product_name: str | None
    price: Decimal
    product_url: str | None
    scraped_at: datetime

    model_config = {"from_attributes": True}


class PriceHistoryResponse(BaseModel):
    alert_id: int
    records: list[PriceRecordResponse]
