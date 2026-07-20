from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class StravaActivity(Base):
    """Strava aktivite (koşu, bisiklet vb.) kayıtları."""
    __tablename__ = "strava_activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    strava_activity_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255), default=None)
    activity_type: Mapped[str | None] = mapped_column(String(50), default=None)  # Run, Ride, Swim, ...
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    distance_m: Mapped[float | None] = mapped_column(Float, default=None)
    moving_time_s: Mapped[int | None] = mapped_column(Integer, default=None)
    elapsed_time_s: Mapped[int | None] = mapped_column(Integer, default=None)
    total_elevation_gain_m: Mapped[float | None] = mapped_column(Float, default=None)
    average_heartrate: Mapped[float | None] = mapped_column(Float, default=None)
    max_heartrate: Mapped[float | None] = mapped_column(Float, default=None)
    calories: Mapped[float | None] = mapped_column(Float, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
