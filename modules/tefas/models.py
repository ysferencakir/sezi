from datetime import datetime

from sqlalchemy import Date, DateTime, Float, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class FundDay(Base):
    """TEFAS günlük fon fiyatı (tefas.gov.tr undocumented backend)."""
    __tablename__ = "fund_days"
    __table_args__ = (
        UniqueConstraint("fund_code", "day", name="uq_fund_day_code_day"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    fund_code: Mapped[str] = mapped_column(String(10), index=True)
    title: Mapped[str | None] = mapped_column(String(255), default=None)
    day: Mapped[datetime] = mapped_column(Date, index=True)
    price: Mapped[float | None] = mapped_column(Float, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
