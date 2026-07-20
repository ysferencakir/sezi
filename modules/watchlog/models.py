from datetime import datetime

from sqlalchemy import Date, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class WatchLog(Base):
    """Telegram'a serbest metinle yazılan izleme kaydı (dizi/film), TMDB ile zenginleştirilmiş."""
    __tablename__ = "watch_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    day: Mapped[datetime] = mapped_column(Date, index=True)
    raw_text: Mapped[str] = mapped_column(String(255))
    season: Mapped[int | None] = mapped_column(Integer, default=None)
    episode: Mapped[int | None] = mapped_column(Integer, default=None)
    # TMDB eşleşmesi
    matched: Mapped[bool] = mapped_column(default=False)
    tmdb_id: Mapped[int | None] = mapped_column(Integer, default=None)
    media_type: Mapped[str | None] = mapped_column(String(10), default=None)  # "movie" | "tv"
    title: Mapped[str | None] = mapped_column(String(255), default=None)
    overview: Mapped[str | None] = mapped_column(String(1000), default=None)
    poster_path: Mapped[str | None] = mapped_column(String(255), default=None)
    release_date: Mapped[str | None] = mapped_column(String(20), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
