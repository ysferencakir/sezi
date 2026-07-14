from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class PlayedTrack(Base):
    """Spotify dinleme geçmişi (recently-played)."""
    __tablename__ = "spotify_played_tracks"

    id: Mapped[int] = mapped_column(primary_key=True)
    spotify_track_id: Mapped[str] = mapped_column(String(64), index=True)
    played_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), unique=True, index=True)
    track_name: Mapped[str] = mapped_column(String(500))
    artist_name: Mapped[str] = mapped_column(String(500))
    album_name: Mapped[str | None] = mapped_column(String(500), default=None)
    duration_ms: Mapped[int | None] = mapped_column(Integer, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
