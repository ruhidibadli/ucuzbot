from datetime import datetime
from pydantic import BaseModel


class UserBase(BaseModel):
    telegram_id: int
    username: str | None = None
    first_name: str | None = None
    language_code: str = "az"


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    id: int
    subscription_tier: str
    max_alerts: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
