from datetime import datetime, timedelta, timezone
from typing import Any

from loguru import logger
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from core.base_module import BaseModule, Schedule
from core.database import AsyncSessionFactory
from core.notifier import notifier
from modules.health import google_fit
from modules.health.models import HealthDay, HeartRate, OAuthToken, SleepSession


class HealthModule(BaseModule):
    name = "health"
    description = "Google Fit üzerinden günlük sağlık verisi (adım, kalori, uyku, nabız)"

    def schedules(self) -> list[Schedule]:
        return [
            Schedule("daily_sync", "0 7 * * *", "run", "Dün'ün sağlık verisini çek"),
            Schedule("morning_report", "30 8 * * *", "morning_report", "Sabah sağlık özeti bildirimi"),
        ]

    # --- Token yönetimi ---

    async def _get_token(self) -> OAuthToken | None:
        async with AsyncSessionFactory() as session:
            result = await session.execute(
                select(OAuthToken).where(OAuthToken.provider == "google")
            )
            return result.scalar_one_or_none()

    async def _fresh_access_token(self) -> str | None:
        token = await self._get_token()
        if token is None:
            logger.warning("[health] Google OAuth token bulunamadı — önce /auth/google ile yetkilendir")
            return None

        if token.expires_at > datetime.now(timezone.utc) + timedelta(minutes=5):
            return token.access_token

        data = await google_fit.refresh_access_token(token.refresh_token)
        async with AsyncSessionFactory() as session:
            token.access_token = data["access_token"]
            token.expires_at = datetime.now(timezone.utc) + timedelta(seconds=data["expires_in"])
            session.add(token)
            await session.commit()

        return data["access_token"]

    # --- BaseModule ---

    async def fetch(self) -> dict[str, Any]:
        access_token = await self._fresh_access_token()
        if not access_token:
            return {}

        yesterday = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        today = yesterday + timedelta(days=1)

        aggregate = await google_fit.fetch_daily_aggregate(access_token, yesterday, today)
        heart = await google_fit.fetch_heart_rate(access_token, yesterday, today)
        sleep = await google_fit.fetch_sleep(access_token, yesterday, today)

        return {"date": yesterday.date(), "aggregate": aggregate, "heart": heart, "sleep": sleep}

    async def process(self, data: dict[str, Any]) -> dict[str, Any]:
        if not data:
            return {}

        day = data["date"]
        summary = self._parse_aggregate(data["aggregate"], day)
        heart_rows = self._parse_heart_rate(data["heart"])
        sleep_rows = self._parse_sleep(data["sleep"])

        async with AsyncSessionFactory() as session:
            # Günlük özet — varsa güncelle
            stmt = insert(HealthDay).values(**summary).on_conflict_do_update(
                index_elements=["day"], set_=summary
            )
            await session.execute(stmt)

            for row in heart_rows:
                session.add(HeartRate(**row))

            for row in sleep_rows:
                session.add(SleepSession(**row))

            await session.commit()

        logger.info(f"[health] {day} kaydedildi — {summary['steps']} adım, {summary['calories']:.0f} kcal")
        return summary

    # --- Bildirim ---

    async def morning_report(self) -> None:
        async with AsyncSessionFactory() as session:
            from datetime import date
            result = await session.execute(
                select(HealthDay).order_by(HealthDay.day.desc()).limit(1)
            )
            row = result.scalar_one_or_none()

        if row is None:
            return

        msg = (
            f"<b>Sabah Sağlık Özeti — {row.day}</b>\n"
            f"👟 Adım: {row.steps:,}\n"
            f"🔥 Kalori: {row.calories:.0f} kcal\n"
            f"⏱ Aktif: {row.active_minutes} dk\n"
            f"📏 Mesafe: {row.distance_meters / 1000:.2f} km"
        )
        await notifier.send(msg, title="Sağlık Özeti")

    # --- Yardımcı parser'lar ---

    def _parse_aggregate(self, raw: dict, day) -> dict:
        result = {"day": day, "steps": 0, "calories": 0.0, "active_minutes": 0, "distance_meters": 0.0}
        mapping = {
            "com.google.step_count.delta": ("steps", "intVal"),
            "com.google.calories.expended": ("calories", "fpVal"),
            "com.google.active_minutes": ("active_minutes", "intVal"),
            "com.google.distance.delta": ("distance_meters", "fpVal"),
        }
        for bucket in raw.get("bucket", []):
            for ds in bucket.get("dataset", []):
                dtype = ds.get("dataSourceId", "")
                for key, (field, val_key) in mapping.items():
                    if key in dtype:
                        for point in ds.get("point", []):
                            for v in point.get("value", []):
                                result[field] += v.get(val_key, 0)
        return result

    def _parse_heart_rate(self, raw: dict) -> list[dict]:
        rows = []
        for point in raw.get("point", []):
            ts_nanos = int(point.get("startTimeNanos", 0))
            bpm = point.get("value", [{}])[0].get("fpVal", 0)
            if bpm:
                rows.append({
                    "measured_at": datetime.fromtimestamp(ts_nanos / 1e9, tz=timezone.utc),
                    "bpm": bpm,
                })
        return rows

    def _parse_sleep(self, raw: dict) -> list[dict]:
        rows = []
        for session in raw.get("session", []):
            start = datetime.fromtimestamp(int(session["startTimeMillis"]) / 1000, tz=timezone.utc)
            end = datetime.fromtimestamp(int(session["endTimeMillis"]) / 1000, tz=timezone.utc)
            duration = int((end - start).total_seconds() / 60)
            rows.append({"start_time": start, "end_time": end, "duration_minutes": duration, "stage": None})
        return rows
