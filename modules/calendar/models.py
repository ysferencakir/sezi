from datetime import datetime

from sqlalchemy import Date, DateTime, Float, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class CalendarDay(Base):
    """Daily meeting aggregate from Google Calendar."""
    __tablename__ = "calendar_days"

    id: Mapped[int] = mapped_column(primary_key=True)
    day: Mapped[datetime] = mapped_column(Date, unique=True, index=True)
    meeting_count: Mapped[int] = mapped_column(Integer, default=0)
    meeting_minutes: Mapped[int] = mapped_column(Integer, default=0)
    busiest_hour: Mapped[int | None] = mapped_column(Integer, default=None)
    free_consecutive_hours: Mapped[float | None] = mapped_column(Float, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
