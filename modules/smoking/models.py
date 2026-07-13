from datetime import datetime

from sqlalchemy import Date, DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class SmokingDay(Base):
    """User-submitted daily cigarette count."""
    __tablename__ = "smoking_days"

    id: Mapped[int] = mapped_column(primary_key=True)
    day: Mapped[datetime] = mapped_column(Date, unique=True, index=True)
    count: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
