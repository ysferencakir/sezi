from datetime import datetime

from sqlalchemy import JSON, Date, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class PowerOutage(Base):
    """EPİAŞ Şeffaflık Platformu — planlı/plansız elektrik kesintisi kaydı.

    Yanıt şeması tam teyit edilemediği için (bkz. epias_client.py notu) alanlar
    ``raw`` içinde kayıpsız saklanıyor; sadece gün ve tür sorgulanabilir sütunda.
    """
    __tablename__ = "power_outages"

    id: Mapped[int] = mapped_column(primary_key=True)
    day: Mapped[datetime] = mapped_column(Date, index=True)
    outage_type: Mapped[str] = mapped_column(String(20), index=True)  # "planned" | "unplanned"
    raw: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
