from datetime import datetime
from pydantic import BaseModel


class PushSubscriptionKeys(BaseModel):
    p256dh: str
    auth: str


class PushSubscribeRequest(BaseModel):
    endpoint: str
    keys: PushSubscriptionKeys
    user_id: int | None = None


class PushUnsubscribeRequest(BaseModel):
    endpoint: str


class PushSubscriptionResponse(BaseModel):
    id: int
    endpoint: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class VapidKeyResponse(BaseModel):
    public_key: str
