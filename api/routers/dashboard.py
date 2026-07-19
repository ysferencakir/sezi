from datetime import date, timedelta

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from core.database import AsyncSessionFactory
from modules.calendar.models import CalendarDay, CalendarEvent
from modules.context.models import WeeklyContext
from modules.currency.models import CurrencyDay
from modules.health.models import HealthDay, HealthRecord, SleepSession
from modules.smoking.models import SmokingDay
from modules.spotify.models import PlayedTrack
from modules.weather.models import WeatherDay

router = APIRouter(prefix="/api", tags=["dashboard"])

HEALTH_DAY_FIELDS = (
    "steps",
    "calories",
    "active_minutes",
    "distance_meters",
    "weight_kg",
    "height_cm",
    "body_fat_percent",
    "nutrition_calories",
    "nutrition_protein_g",
    "nutrition_fat_g",
    "nutrition_carbs_g",
    "blood_pressure_systolic",
    "blood_pressure_diastolic",
    "blood_glucose_mmol",
    "oxygen_saturation_percent",
    "hydration_liters",
    "resting_heart_rate",
    "hrv_rmssd_ms",
    "respiratory_rate",
    "vo2_max",
    "floors_climbed",
    "body_temperature_celsius",
)


def _health_day_dict(row: HealthDay) -> dict:
    return {
        "day": row.day.isoformat(),
        **{field: getattr(row, field) for field in HEALTH_DAY_FIELDS},
    }


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
        "health": None if health is None else _health_day_dict(health),
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
            "sunrise": weather.sunrise.isoformat() if weather.sunrise else None,
            "sunset": weather.sunset.isoformat() if weather.sunset else None,
            "day_length_minutes": weather.day_length_minutes,
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


@router.get("/history")
async def get_history(days: int = 30):
    """Son N günün gün bazlı serileri — dashboard trend grafiklerini besler."""
    days = max(1, min(days, 365))
    since = date.today() - timedelta(days=days)

    async with AsyncSessionFactory() as session:
        health_rows = (
            await session.execute(
                select(HealthDay).where(HealthDay.day >= since).order_by(HealthDay.day)
            )
        ).scalars().all()
        calendar_rows = (
            await session.execute(
                select(CalendarDay).where(CalendarDay.day >= since).order_by(CalendarDay.day)
            )
        ).scalars().all()
        weather_rows = (
            await session.execute(
                select(WeatherDay).where(WeatherDay.day >= since).order_by(WeatherDay.day)
            )
        ).scalars().all()
        smoking_rows = (
            await session.execute(
                select(SmokingDay).where(SmokingDay.day >= since).order_by(SmokingDay.day)
            )
        ).scalars().all()
        currency_rows = (
            await session.execute(
                select(CurrencyDay).where(CurrencyDay.day >= since).order_by(CurrencyDay.day)
            )
        ).scalars().all()
        # Uyku evre bazlı segmentlerden toplanır; "awake" süresi uykuya sayılmaz.
        sleep_rows = (
            await session.execute(
                select(
                    func.date(SleepSession.end_time).label("day"),
                    func.sum(SleepSession.duration_minutes),
                )
                .where(
                    func.date(SleepSession.end_time) >= since,
                    (SleepSession.stage.is_(None)) | (SleepSession.stage != "awake"),
                )
                .group_by(func.date(SleepSession.end_time))
                .order_by(func.date(SleepSession.end_time))
            )
        ).all()
        spotify_rows = (
            await session.execute(
                select(
                    func.date(PlayedTrack.played_at).label("day"),
                    func.count(PlayedTrack.id),
                )
                .where(func.date(PlayedTrack.played_at) >= since)
                .group_by(func.date(PlayedTrack.played_at))
                .order_by(func.date(PlayedTrack.played_at))
            )
        ).all()

    def iso(day) -> str:
        return day.isoformat() if isinstance(day, date) else str(day)

    return {
        "since": since.isoformat(),
        "health": [
            _health_day_dict(row)
            for row in health_rows
        ],
        "sleep": [{"day": iso(day), "minutes": int(minutes)} for day, minutes in sleep_rows],
        "calendar": [
            {
                "day": row.day.isoformat(),
                "meeting_count": row.meeting_count,
                "meeting_minutes": row.meeting_minutes,
            }
            for row in calendar_rows
        ],
        "weather": [
            {
                "day": row.day.isoformat(),
                "temp_min": row.temp_min,
                "temp_max": row.temp_max,
                "european_aqi": row.european_aqi,
                "precipitation_mm": row.precipitation_mm,
            }
            for row in weather_rows
        ],
        "smoking": [{"day": row.day.isoformat(), "count": row.count} for row in smoking_rows],
        "currency": [
            {"day": row.day.isoformat(), "usd_try": row.usd_try, "eur_try": row.eur_try}
            for row in currency_rows
        ],
        "spotify": [{"day": iso(day), "plays": plays} for day, plays in spotify_rows],
    }


@router.get("/health/records")
async def get_health_records(
    days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=500, ge=1, le=2000),
    category: str | None = None,
    record_type: str | None = None,
):
    """Health Connect'ten gelen tüm kayıt türlerini filtrelenebilir şekilde döndürür."""
    since = date.today() - timedelta(days=days)
    query = select(HealthRecord).where(func.date(HealthRecord.start_time) >= since)
    if category:
        query = query.where(HealthRecord.category == category)
    if record_type:
        query = query.where(HealthRecord.record_type == record_type)
    query = query.order_by(HealthRecord.start_time.desc(), HealthRecord.id.desc()).limit(limit)

    async with AsyncSessionFactory() as session:
        rows = (await session.execute(query)).scalars().all()

    categories: dict[str, int] = {}
    record_types: dict[str, int] = {}
    for row in rows:
        categories[row.category] = categories.get(row.category, 0) + 1
        record_types[row.record_type] = record_types.get(row.record_type, 0) + 1

    return {
        "since": since.isoformat(),
        "count": len(rows),
        "categories": categories,
        "record_types": record_types,
        "records": [
            {
                "external_id": row.external_id,
                "record_type": row.record_type,
                "category": row.category,
                "title": row.title,
                "start_time": row.start_time.isoformat() if row.start_time else None,
                "end_time": row.end_time.isoformat() if row.end_time else None,
                "value": row.value,
                "unit": row.unit,
                "data": row.data or {},
            }
            for row in rows
        ],
    }


@router.get("/spotify/recent")
async def get_recent_tracks(limit: int = 10):
    """Son çalınan şarkılar — dashboard 'Bugün' sekmesi için."""
    limit = max(1, min(limit, 50))
    async with AsyncSessionFactory() as session:
        rows = (
            await session.execute(
                select(PlayedTrack).order_by(PlayedTrack.played_at.desc()).limit(limit)
            )
        ).scalars().all()

    return {
        "tracks": [
            {
                "played_at": row.played_at.isoformat(),
                "track_name": row.track_name,
                "artist_name": row.artist_name,
            }
            for row in rows
        ]
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
