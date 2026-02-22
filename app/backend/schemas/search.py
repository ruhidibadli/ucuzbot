from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel


class SearchResult(BaseModel):
    product_name: str
    price: Decimal
    product_url: str
    store_slug: str
    store_name: str
    image_url: str | None = None
    in_stock: bool = True


class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: list[SearchResult]
    errors: list[str] = []
    searched_at: datetime
