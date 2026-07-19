from datetime import date, datetime

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from core.config import settings
from core.database import AsyncSessionFactory
from modules.health.models import HealthDay, HeartRate, SleepSession

router = APIRouter(prefix="/api/health", tags=["ingest"])


class DayPayload(BaseModel):
    day: date
    steps: int | None = None
    calories: float | None = None
    active_minutes: int | None = None
    distance_meters: float | None = None
    weight_kg: float | None = None
    body_fat_percent: float | None = None
    blood_pressure_systolic: float | None = None
    blood_pressure_diastolic: float | None = None
    oxygen_saturation_percent: float | None = None
    hydration_liters: float | None = None


class SleepPayload(BaseModel):
    start_time: datetime
    end_time: datetime
    stage: str | None = None  # awake/light/deep/rem — Health Connect evreleriyle uyumlu


class HeartRatePayload(BaseModel):
    measured_at: datetime
    bpm: float


class IngestPayload(BaseModel):
    source: str = Field(default="health_connect", max_length=50)
    days: list[DayPayload] = []
    sleep_sessions: list[SleepPayload] = []
    heart_rates: list[HeartRatePayload] = []


def _check_token(token: str | None) -> None:
    if not settings.health_ingest_token:
        raise HTTPException(status_code=503, detail="Ingest disabled: HEALTH_INGEST_TOKEN not configured")
    if token != settings.health_ingest_token:
        raise HTTPException(status_code=401, detail="Invalid ingest token")


@router.post("/ingest")
async def ingest_health(payload: IngestPayload, x_ingest_token: str | None = Header(default=None)):
    """Health Connect köprü uygulamasından (veya başka bir istemciden) sağlık verisi alır.

    Google Fit senkronuyla paralel çalışabilir: gün kayıtları upsert edilir ve
    yalnızca gönderilen alanlar yazılır, None alanlar mevcut değeri ezmez.
    """
    _check_token(x_ingest_token)

    days_upserted = 0
    sleep_added = 0
    sleep_skipped = 0
    hr_added = 0
    hr_skipped = 0

    async with AsyncSessionFactory() as session:
        for d in payload.days:
            values = d.model_dump(exclude_none=True)
            stmt = insert(HealthDay).values(**values).on_conflict_do_update(
                index_elements=["day"], set_={k: v for k, v in values.items() if k != "day"}
            )
            await session.execute(stmt)
            days_upserted += 1

        if payload.sleep_sessions:
            starts = [s.start_time for s in payload.sleep_sessions]
            existing = {
                (row.start_time, row.end_time, row.stage)
                for row in (
                    await session.execute(
                        select(SleepSession).where(SleepSession.start_time.in_(starts))
                    )
                ).scalars()
            }
            for s in payload.sleep_sessions:
                key = (s.start_time, s.end_time, s.stage)
                if key in existing:
                    sleep_skipped += 1
                    continue
                session.add(
                    SleepSession(
                        start_time=s.start_time,
                        end_time=s.end_time,
                        duration_minutes=int((s.end_time - s.start_time).total_seconds() // 60),
                        stage=s.stage,
                    )
                )
                existing.add(key)
                sleep_added += 1

        if payload.heart_rates:
            measured = [h.measured_at for h in payload.heart_rates]
            existing_hr = {
                row.measured_at
                for row in (
                    await session.execute(
                        select(HeartRate).where(HeartRate.measured_at.in_(measured))
                    )
                ).scalars()
            }
            for h in payload.heart_rates:
                if h.measured_at in existing_hr:
                    hr_skipped += 1
                    continue
                session.add(HeartRate(measured_at=h.measured_at, bpm=h.bpm))
                existing_hr.add(h.measured_at)
                hr_added += 1

        await session.commit()

    return {
        "status": "ok",
        "source": payload.source,
        "days_upserted": days_upserted,
        "sleep_added": sleep_added,
        "sleep_skipped": sleep_skipped,
        "heart_rates_added": hr_added,
        "heart_rates_skipped": hr_skipped,
    }
