from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    ARRAY,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.backend.db.base import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    push_subscription_id: Mapped[int | None] = mapped_column(
        ForeignKey("push_subscriptions.id", ondelete="SET NULL"), nullable=True
    )
    search_query: Mapped[str] = mapped_column(String(500), nullable=False)
    target_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    store_slugs: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_triggered: Mapped[bool] = mapped_column(Boolean, default=False)
    triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    lowest_price_found: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    lowest_price_store: Mapped[str | None] = mapped_column(String(50))
    lowest_price_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User | None"] = relationship(back_populates="alerts")  # noqa: F821
    push_subscription: Mapped["PushSubscription | None"] = relationship()  # noqa: F821
    price_records: Mapped[list["PriceRecord"]] = relationship(  # noqa: F821
        back_populates="alert", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_alerts_user_id", "user_id"),
        Index("idx_alerts_active", "is_active", postgresql_where=(is_active == True)),  # noqa: E712
    )
