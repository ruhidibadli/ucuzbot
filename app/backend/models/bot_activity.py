from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.backend.db.base import Base


class BotActivity(Base):
    __tablename__ = "bot_activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("idx_bot_activities_created_at", "created_at"),
    )


async def log_bot_activity(
    session: AsyncSession,
    user_id: int | None,
    telegram_id: int | None,
    action: str,
    detail: str | None = None,
) -> None:
    session.add(BotActivity(
        user_id=user_id,
        telegram_id=telegram_id,
        action=action,
        detail=detail,
    ))
