from datetime import datetime

from sqlalchemy import Date, DateTime, Float, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class CurrencyDay(Base):
    """Daily USD/EUR -> TRY reference rates from Frankfurter (ECB)."""
    __tablename__ = "currency_days"

    id: Mapped[int] = mapped_column(primary_key=True)
    day: Mapped[datetime] = mapped_column(Date, unique=True, index=True)
    usd_try: Mapped[float | None] = mapped_column(Float, default=None)
    eur_try: Mapped[float | None] = mapped_column(Float, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
