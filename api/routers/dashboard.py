from datetime import date, timedelta

from fastapi import APIRouter
from sqlalchemy import func, select

from core.database import AsyncSessionFactory
from modules.calendar.models import CalendarDay, CalendarEvent
from modules.context.models import WeeklyContext
from modules.currency.models import CurrencyDay
from modules.health.models import HealthDay
from modules.smoking.models import SmokingDay
from modules.weather.models import WeatherDay

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
        weather = (
            await session.execute(select(WeatherDay).order_by(WeatherDay.day.desc()).limit(1))
        ).scalar_one_or_none()
        smoking = (
            await session.execute(select(SmokingDay).order_by(SmokingDay.day.desc()).limit(1))
        ).scalar_one_or_none()
        currency = (
            await session.execute(select(CurrencyDay).order_by(CurrencyDay.day.desc()).limit(1))
        ).scalar_one_or_none()

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
            "is_holiday": calendar.is_holiday,
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
        "weather": None if weather is None else {
            "day": weather.day.isoformat(),
            "condition": weather.condition,
            "temp_min": weather.temp_min,
            "temp_max": weather.temp_max,
            "precipitation_mm": weather.precipitation_mm,
            "european_aqi": weather.european_aqi,
            "pm2_5": weather.pm2_5,
            "pm10": weather.pm10,
            "uv_index_max": weather.uv_index_max,
        },
        "smoking": None if smoking is None else {
            "day": smoking.day.isoformat(),
            "count": smoking.count,
        },
        "currency": None if currency is None else {
            "day": currency.day.isoformat(),
            "usd_try": currency.usd_try,
            "eur_try": currency.eur_try,
        },
    }


@router.get("/calendar/categories")
async def get_category_breakdown(days: int = 7):
    """Son N gündeki takvim etkinliklerinin kategori bazında toplam dakikası."""
    since = date.today() - timedelta(days=days)
    async with AsyncSessionFactory() as session:
        result = await session.execute(
            select(CalendarEvent.category, func.sum(CalendarEvent.duration_minutes))
            .where(CalendarEvent.day >= since)
            .group_by(CalendarEvent.category)
            .order_by(func.sum(CalendarEvent.duration_minutes).desc())
        )
        rows = result.all()

    return {
        "since": since.isoformat(),
        "categories": [{"category": cat, "minutes": int(minutes)} for cat, minutes in rows],
    }
