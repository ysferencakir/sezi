from datetime import datetime, timedelta, timezone
from typing import Any

from loguru import logger
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from core.base_module import BaseModule, Schedule
from core.database import AsyncSessionFactory
from modules.health import google_fit
from modules.health.models import HealthDay, HeartRate, OAuthToken, SleepSession, Workout


class HealthModule(BaseModule):
    name = "health"
    description = "Google Fit üzerinden günlük sağlık verisi (adım, kalori, uyku, nabız)"

    def schedules(self) -> list[Schedule]:
        return [
            Schedule("daily_sync", "0 7 * * *", "run", "Dün'ün sağlık verisini çek"),
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
        sleep_stages = await google_fit.fetch_sleep_stages(access_token, yesterday, today)
        sessions = await google_fit.fetch_sessions(access_token, yesterday, today)

        return {
            "date": yesterday.date(),
            "aggregate": aggregate,
            "heart": heart,
            "sleep": sleep,
            "sleep_stages": sleep_stages,
            "sessions": sessions,
        }

    async def process(self, data: dict[str, Any]) -> dict[str, Any]:
        if not data:
            return {}

        day = data["date"]
        summary = self._parse_aggregate(data["aggregate"], day)
        heart_rows = self._parse_heart_rate(data["heart"])
        sleep_rows = self._parse_sleep(data["sleep"], data["sleep_stages"])
        workout_rows = self._parse_workouts(data["sessions"])

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

            for row in workout_rows:
                stmt = insert(Workout).values(**row).on_conflict_do_update(
                    index_elements=["google_session_id"], set_=row
                )
                await session.execute(stmt)

            await session.commit()

        logger.info(f"[health] {day} kaydedildi — {summary['steps']} adım, {summary['calories']:.0f} kcal")
        return summary

    # --- Yardımcı parser'lar ---

    def _parse_aggregate(self, raw: dict, day) -> dict:
        result = {
            "day": day, "steps": 0, "calories": 0.0, "active_minutes": 0, "distance_meters": 0.0,
            "weight_kg": None, "height_cm": None, "body_fat_percent": None,
            "nutrition_calories": None, "nutrition_protein_g": None,
            "nutrition_fat_g": None, "nutrition_carbs_g": None,
            "blood_pressure_systolic": None, "blood_pressure_diastolic": None,
            "blood_glucose_mmol": None, "oxygen_saturation_percent": None,
            "hydration_liters": None,
        }
        # Basit sayısal alanlar: (dataType anahtarı, sonuç alanı, value key, "sum" | "last")
        simple_fields = [
            ("com.google.step_count.delta", "steps", "intVal", "sum"),
            ("com.google.calories.expended", "calories", "fpVal", "sum"),
            ("com.google.active_minutes", "active_minutes", "intVal", "sum"),
            ("com.google.distance.delta", "distance_meters", "fpVal", "sum"),
            ("com.google.weight", "weight_kg", "fpVal", "last"),
            ("com.google.height", "height_cm", "fpVal", "last"),
            ("com.google.body.fat.percentage", "body_fat_percent", "fpVal", "last"),
            ("com.google.blood_glucose", "blood_glucose_mmol", "fpVal", "last"),
            ("com.google.oxygen_saturation", "oxygen_saturation_percent", "fpVal", "last"),
            ("com.google.hydration", "hydration_liters", "fpVal", "sum"),
        ]
        # height gelir metre cinsinden — cm'e çevirmek için sonradan *100 yapılır.

        for bucket in raw.get("bucket", []):
            for ds in bucket.get("dataset", []):
                dtype = ds.get("dataSourceId", "")
                points = ds.get("point", [])

                for key, field, val_key, strategy in simple_fields:
                    if key not in dtype:
                        continue
                    for point in points:
                        for v in point.get("value", []):
                            val = v.get(val_key, 0)
                            if strategy == "sum":
                                result[field] = (result[field] or 0) + val
                            else:  # last
                                result[field] = val

                if "com.google.nutrition" in dtype:
                    for point in points:
                        for v in point.get("value", []):
                            for entry in v.get("mapVal", []):
                                key = entry.get("key")
                                val = entry.get("value", {}).get("fpVal", 0)
                                if key == "calories":
                                    result["nutrition_calories"] = (result["nutrition_calories"] or 0) + val
                                elif key == "protein":
                                    result["nutrition_protein_g"] = (result["nutrition_protein_g"] or 0) + val
                                elif key == "fat.total":
                                    result["nutrition_fat_g"] = (result["nutrition_fat_g"] or 0) + val
                                elif key == "carbs.total":
                                    result["nutrition_carbs_g"] = (result["nutrition_carbs_g"] or 0) + val

                if "com.google.blood_pressure" in dtype:
                    for point in points:
                        for v in point.get("value", []):
                            for entry in v.get("mapVal", []):
                                key = entry.get("key")
                                val = entry.get("value", {}).get("fpVal")
                                if key == "systolic":
                                    result["blood_pressure_systolic"] = val
                                elif key == "diastolic":
                                    result["blood_pressure_diastolic"] = val

        if result["height_cm"] is not None:
            result["height_cm"] = round(result["height_cm"] * 100, 1)

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

    def _parse_sleep(self, sessions_raw: dict, stages_raw: dict) -> list[dict]:
        stage_points = stages_raw.get("point", [])
        if stage_points:
            # Evre bazlı — her segment ayrı bir satır, gerçek stage adıyla.
            rows = []
            for point in stage_points:
                start = datetime.fromtimestamp(int(point.get("startTimeNanos", 0)) / 1e9, tz=timezone.utc)
                end = datetime.fromtimestamp(int(point.get("endTimeNanos", 0)) / 1e9, tz=timezone.utc)
                stage_code = point.get("value", [{}])[0].get("intVal")
                rows.append({
                    "start_time": start,
                    "end_time": end,
                    "duration_minutes": int((end - start).total_seconds() / 60),
                    "stage": google_fit.SLEEP_STAGES.get(stage_code, f"unknown_{stage_code}"),
                })
            return rows

        # Evre verisi yoksa (cihaz üretmiyor) session bazlı kaba özet — stage bilinmiyor.
        rows = []
        for session in sessions_raw.get("session", []):
            start = datetime.fromtimestamp(int(session["startTimeMillis"]) / 1000, tz=timezone.utc)
            end = datetime.fromtimestamp(int(session["endTimeMillis"]) / 1000, tz=timezone.utc)
            duration = int((end - start).total_seconds() / 60)
            rows.append({"start_time": start, "end_time": end, "duration_minutes": duration, "stage": None})
        return rows

    def _parse_workouts(self, sessions_raw: dict) -> list[dict]:
        rows = []
        for session in sessions_raw.get("session", []):
            activity_type = session.get("activityType")
            if activity_type == 72:  # sleep — ayrı SleepSession'da tutuluyor
                continue
            start = datetime.fromtimestamp(int(session["startTimeMillis"]) / 1000, tz=timezone.utc)
            end = datetime.fromtimestamp(int(session["endTimeMillis"]) / 1000, tz=timezone.utc)
            rows.append({
                "google_session_id": session["id"],
                "activity_type": google_fit.activity_type_name(activity_type),
                "name": session.get("name") or None,
                "start_time": start,
                "end_time": end,
                "duration_minutes": int((end - start).total_seconds() / 60),
            })
        return rows
