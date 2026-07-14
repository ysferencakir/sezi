from datetime import datetime

from sqlalchemy import Boolean, Date, DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class CalendarEvent(Base):
    """Raw calendar event with a keyword-derived category — powers category breakdowns."""
    __tablename__ = "calendar_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    google_event_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    day: Mapped[datetime] = mapped_column(Date, index=True)
    title: Mapped[str] = mapped_column(String(500))
    category: Mapped[str] = mapped_column(String(50), index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration_minutes: Mapped[int] = mapped_column(Integer)
    all_day: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str | None] = mapped_column(String(2000), default=None)
    location: Mapped[str | None] = mapped_column(String(500), default=None)
    attendee_count: Mapped[int | None] = mapped_column(Integer, default=None)
    organizer_email: Mapped[str | None] = mapped_column(String(255), default=None)
    recurring_event_id: Mapped[str | None] = mapped_column(String(255), default=None)
    color_id: Mapped[str | None] = mapped_column(String(10), default=None)
    meet_link: Mapped[str | None] = mapped_column(String(500), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class CalendarDay(Base):
    """Daily meeting aggregate from Google Calendar."""
    __tablename__ = "calendar_days"

    id: Mapped[int] = mapped_column(primary_key=True)
    day: Mapped[datetime] = mapped_column(Date, unique=True, index=True)
    meeting_count: Mapped[int] = mapped_column(Integer, default=0)
    meeting_minutes: Mapped[int] = mapped_column(Integer, default=0)
    busiest_hour: Mapped[int | None] = mapped_column(Integer, default=None)
    free_consecutive_hours: Mapped[float | None] = mapped_column(Float, default=None)
    is_holiday: Mapped[bool] = mapped_column(Boolean, default=False)
    holiday_name: Mapped[str | None] = mapped_column(String(255), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
