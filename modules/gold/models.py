from datetime import datetime

from sqlalchemy import JSON, Date, DateTime, Float, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class GoldDay(Base):
    """Günlük altın anlık görüntüsü — altinapi.com (Harem Altın verisi).

    Sık kullanılan enstrümanlar sorgulanabilir sütunlarda, tüm kategori
    (ALTIN + SARRAFIYE) yanıtı ise ``raw`` alanında kayıpsız saklanır.
    """
    __tablename__ = "gold_days"

    id: Mapped[int] = mapped_column(primary_key=True)
    day: Mapped[datetime] = mapped_column(Date, unique=True, index=True)
    gram_altin_alis: Mapped[float | None] = mapped_column(Float, default=None)
    gram_altin_satis: Mapped[float | None] = mapped_column(Float, default=None)
    ceyrek_alis: Mapped[float | None] = mapped_column(Float, default=None)
    ceyrek_satis: Mapped[float | None] = mapped_column(Float, default=None)
    yarim_alis: Mapped[float | None] = mapped_column(Float, default=None)
    yarim_satis: Mapped[float | None] = mapped_column(Float, default=None)
    tam_alis: Mapped[float | None] = mapped_column(Float, default=None)
    tam_satis: Mapped[float | None] = mapped_column(Float, default=None)
    ata_alis: Mapped[float | None] = mapped_column(Float, default=None)
    ata_satis: Mapped[float | None] = mapped_column(Float, default=None)
    raw: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
