from fastapi import APIRouter
from sqlalchemy import select

from core.database import AsyncSessionFactory
from modules.calendar.models import CalendarDay
from modules.context.models import WeeklyContext
from modules.health.models import HealthDay

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/summary")
async def get_summary():
    """Latest snapshot from every module — powers the placeholder dashboard."""
    async with AsyncSessionFactory() as session:
        health = (
            await session.execute(select(HealthDay).order_by(HealthDay.day.desc()).limit(1))
        ).scalar_one_or_none()
        calendar = (
            await session.execute(select(CalendarDay).order_by(CalendarDay.day.desc()).limit(1))
        ).scalar_one_or_none()
        context_rows = (
            await session.execute(
                select(WeeklyContext).order_by(WeeklyContext.week_start.desc()).limit(4)
            )
        ).scalars().all()

    return {
        "health": None if health is None else {
            "day": health.day.isoformat(),
            "steps": health.steps,
            "calories": health.calories,
            "active_minutes": health.active_minutes,
            "distance_meters": health.distance_meters,
        },
        "calendar": None if calendar is None else {
            "day": calendar.day.isoformat(),
            "meeting_count": calendar.meeting_count,
            "meeting_minutes": calendar.meeting_minutes,
            "busiest_hour": calendar.busiest_hour,
            "free_consecutive_hours": calendar.free_consecutive_hours,
        },
        "context": [
            {
                "week_start": row.week_start.isoformat(),
                "notes": row.notes,
                "special_events": row.special_events,
                "general_feeling": row.general_feeling,
            }
            for row in context_rows
        ],
    }
