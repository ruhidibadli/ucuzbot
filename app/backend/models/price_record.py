from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.backend.db.base import Base


class PriceRecord(Base):
    __tablename__ = "price_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id", ondelete="CASCADE"))
    store_slug: Mapped[str] = mapped_column(String(50), nullable=False)
    product_name: Mapped[str | None] = mapped_column(String(1000))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    product_url: Mapped[str | None] = mapped_column(Text)
    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    alert: Mapped["Alert"] = relationship(back_populates="price_records")  # noqa: F821

    __table_args__ = (
        Index("idx_price_records_alert_id", "alert_id"),
        Index("idx_price_records_scraped_at", "scraped_at"),
    )
