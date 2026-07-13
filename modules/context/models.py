from datetime import datetime

from sqlalchemy import Date, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class WeeklyContext(Base):
    """User-submitted weekly reflection notes."""
    __tablename__ = "weekly_context"

    id: Mapped[int] = mapped_column(primary_key=True)
    week_start: Mapped[datetime] = mapped_column(Date, unique=True, index=True)
    notes: Mapped[str] = mapped_column(Text)
    special_events: Mapped[str | None] = mapped_column(String(500), default=None)
    general_feeling: Mapped[int | None] = mapped_column(Integer, default=None)  # 1-10
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
