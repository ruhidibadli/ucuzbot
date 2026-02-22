from datetime import datetime

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    email: str = Field(max_length=255)
    password: str = Field(min_length=6, max_length=128)
    first_name: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class UserProfile(BaseModel):
    id: int
    email: str | None
    first_name: str | None
    language_code: str
    subscription_tier: str
    max_alerts: int
    created_at: datetime

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile
