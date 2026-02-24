from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.api.dependencies import get_current_user, get_db
from app.backend.core.auth import create_jwt, hash_password, verify_password
from app.backend.core.config import settings
from app.backend.models.user import User
from app.backend.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserProfile

router = APIRouter()


def _make_profile(user: User) -> UserProfile:
    admin_email = settings.ADMIN_EMAIL.strip().lower()
    is_admin = bool(admin_email and user.email and user.email.lower() == admin_email)
    return UserProfile.model_validate(user).model_copy(update={"is_admin": is_admin})


@router.post("/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    email = data.email.strip().lower()

    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=email,
        password_hash=hash_password(data.password),
        first_name=data.first_name,
    )
    db.add(user)
    await db.flush()

    token = create_jwt(user.id)
    await db.commit()
    return AuthResponse(
        access_token=token,
        user=_make_profile(user),
    )


@router.post("/auth/login", response_model=AuthResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    email = data.email.strip().lower()

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not user.password_hash or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    token = create_jwt(user.id)
    return AuthResponse(
        access_token=token,
        user=_make_profile(user),
    )


@router.get("/auth/me", response_model=UserProfile)
async def me(user: User = Depends(get_current_user)):
    return _make_profile(user)
