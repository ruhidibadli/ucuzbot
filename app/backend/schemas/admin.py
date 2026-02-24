from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class AdminStatsResponse(BaseModel):
    total_users: int
    total_alerts: int
    active_alerts: int
    triggered_alerts: int
    inactive_alerts: int
    alerts_by_store: dict[str, int]
    recent_triggered_count_24h: int
    recent_triggered_count_7d: int


class AdminUserListItem(BaseModel):
    id: int
    email: str | None
    telegram_id: int | None
    first_name: str | None
    subscription_tier: str
    alert_count: int
    active_alert_count: int
    triggered_alert_count: int
    is_active: bool
    created_at: datetime


class AdminUserListResponse(BaseModel):
    users: list[AdminUserListItem]
    total: int
    page: int
    page_size: int


class AdminAlertListItem(BaseModel):
    id: int
    user_id: int | None
    user_email: str | None
    user_first_name: str | None
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


class AdminAlertListResponse(BaseModel):
    alerts: list[AdminAlertListItem]
    total: int
    page: int
    page_size: int
