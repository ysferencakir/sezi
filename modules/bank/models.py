from datetime import datetime

from sqlalchemy import Date, DateTime, Float, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class BankAccountSnapshot(Base):
    """Kobaküs Open Banking üzerinden günlük hesap bakiyesi anlık görüntüsü."""
    __tablename__ = "bank_account_snapshots"
    __table_args__ = (
        UniqueConstraint("day", "iban", name="uq_bank_snapshot_day_iban"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    day: Mapped[datetime] = mapped_column(Date, index=True)
    bank_name: Mapped[str | None] = mapped_column(String(100), default=None)
    iban: Mapped[str] = mapped_column(String(50), index=True)  # Kobaküs maskeli döner (ör. TR•••4821)
    balance: Mapped[float | None] = mapped_column(Float, default=None)
    currency: Mapped[str | None] = mapped_column(String(10), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
