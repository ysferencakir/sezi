from datetime import date, timedelta

from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy import select

from core.database import AsyncSessionFactory
from modules.context import service
from modules.context.models import WeeklyContext

router = APIRouter(prefix="/api", tags=["context"])


class ContextEntry(BaseModel):
    week_start: date
    notes: str
    special_events: str | None = None
    general_feeling: int | None = Field(default=None, ge=1, le=10)


@router.post("/context")
async def submit_context_endpoint(entry: ContextEntry):
    """Submit or update weekly context notes."""
    await service.submit_context(
        week_start=entry.week_start,
        notes=entry.notes,
        special_events=entry.special_events,
        general_feeling=entry.general_feeling,
    )
    return {"status": "success", "week_start": entry.week_start.isoformat()}


@router.get("/context")
async def get_context(week_start: date | None = None):
    """Get context notes. Defaults to last 4 weeks if no week_start given."""
    if week_start is None:
        week_start = date.today() - timedelta(days=21)

    async with AsyncSessionFactory() as session:
        result = await session.execute(
            select(WeeklyContext)
            .where(WeeklyContext.week_start >= week_start)
            .order_by(WeeklyContext.week_start.desc())
        )
        rows = result.scalars().all()

    return {
        "context": [
            {
                "week_start": row.week_start.isoformat(),
                "notes": row.notes,
                "special_events": row.special_events,
                "general_feeling": row.general_feeling,
            }
            for row in rows
        ]
    }
