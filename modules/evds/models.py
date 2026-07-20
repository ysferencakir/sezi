from datetime import datetime

from sqlalchemy import Date, DateTime, Float, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class EvdsDay(Base):
    """TCMB EVDS resmi günlük USD/EUR alış-satış kuru (Frankfurter/ECB'den bağımsız resmi kaynak)."""
    __tablename__ = "evds_days"

    id: Mapped[int] = mapped_column(primary_key=True)
    day: Mapped[datetime] = mapped_column(Date, unique=True, index=True)
    usd_alis: Mapped[float | None] = mapped_column(Float, default=None)
    usd_satis: Mapped[float | None] = mapped_column(Float, default=None)
    eur_alis: Mapped[float | None] = mapped_column(Float, default=None)
    eur_satis: Mapped[float | None] = mapped_column(Float, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
