from datetime import datetime

from sqlalchemy import BigInteger, Date, DateTime, Float, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class StockDay(Base):
    """Yahoo Finance (query1.finance.yahoo.com) üzerinden günlük hisse/endeks kapanışı."""
    __tablename__ = "stock_days"
    __table_args__ = (
        UniqueConstraint("symbol", "day", name="uq_stock_day_symbol_day"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True)  # ör. "ISCTR.IS", "XU100.IS"
    day: Mapped[datetime] = mapped_column(Date, index=True)
    open: Mapped[float | None] = mapped_column(Float, default=None)
    high: Mapped[float | None] = mapped_column(Float, default=None)
    low: Mapped[float | None] = mapped_column(Float, default=None)
    close: Mapped[float | None] = mapped_column(Float, default=None)
    volume: Mapped[int | None] = mapped_column(BigInteger, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
