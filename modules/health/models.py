from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class OAuthToken(Base):
    """Google OAuth2 token storage."""
    __tablename__ = "oauth_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(32), unique=True)  # "google"
    access_token: Mapped[str] = mapped_column(Text)
    refresh_token: Mapped[str] = mapped_column(Text)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class HealthDay(Base):
    """Günlük sağlık özeti (adım, kalori, aktif süre, mesafe)."""
    __tablename__ = "health_days"
    __table_args__ = (UniqueConstraint("day"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    day: Mapped[date] = mapped_column(Date, index=True)
    steps: Mapped[int] = mapped_column(Integer, default=0)
    calories: Mapped[float] = mapped_column(Float, default=0.0)
    active_minutes: Mapped[int] = mapped_column(Integer, default=0)
    distance_meters: Mapped[float] = mapped_column(Float, default=0.0)


class HeartRate(Base):
    """Anlık kalp atış hızı ölçümleri."""
    __tablename__ = "heart_rates"

    id: Mapped[int] = mapped_column(primary_key=True)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    bpm: Mapped[float] = mapped_column(Float)


class SleepSession(Base):
    """Uyku seansları."""
    __tablename__ = "sleep_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration_minutes: Mapped[int] = mapped_column(Integer)
    stage: Mapped[str | None] = mapped_column(String(32), default=None)  # light, deep, rem, awake
