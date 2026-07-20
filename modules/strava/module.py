from datetime import datetime, timedelta, timezone
from typing import Any

from loguru import logger
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from core.base_module import BaseModule, Schedule
from core.database import AsyncSessionFactory
from modules.health.models import OAuthToken
from modules.strava import strava_client
from modules.strava.models import StravaActivity


class StravaModule(BaseModule):
    name = "strava"
    description = "Strava aktivite geçmişi"

    def schedules(self) -> list[Schedule]:
        return [
            Schedule("daily_sync", "10 7 * * *", "run", "Son 24 saatte kaydedilen aktiviteleri çek"),
        ]

    async def _get_token(self) -> OAuthToken | None:
        async with AsyncSessionFactory() as session:
            result = await session.execute(
                select(OAuthToken).where(OAuthToken.provider == "strava")
            )
            return result.scalar_one_or_none()

    async def _fresh_access_token(self) -> str | None:
        token = await self._get_token()
        if token is None:
            logger.warning("[strava] OAuth token bulunamadı — önce /auth/strava/authorize ile yetkilendir")
            return None

        if token.expires_at > datetime.now(timezone.utc) + timedelta(minutes=5):
            return token.access_token

        data = await strava_client.refresh_access_token(token.refresh_token)
        async with AsyncSessionFactory() as session:
            token.access_token = data["access_token"]
            token.expires_at = datetime.now(timezone.utc) + timedelta(seconds=data["expires_in"])
            if data.get("refresh_token"):
                token.refresh_token = data["refresh_token"]
            session.add(token)
            await session.commit()

        return data["access_token"]

    async def _last_start_date(self) -> datetime | None:
        async with AsyncSessionFactory() as session:
            result = await session.execute(
                select(StravaActivity).order_by(StravaActivity.start_date.desc()).limit(1)
            )
            row = result.scalar_one_or_none()
            return row.start_date if row else None

    async def fetch(self) -> dict[str, Any]:
        access_token = await self._fresh_access_token()
        if not access_token:
            return {}

        last_start = await self._last_start_date()
        after = last_start or (datetime.now(timezone.utc) - timedelta(days=1))
        activities = await strava_client.fetch_activities(access_token, int(after.timestamp()))
        return {"activities": activities}

    async def process(self, data: dict[str, Any]) -> dict[str, Any]:
        activities = data.get("activities", [])
        if not activities:
            return {}

        rows = [self._parse_activity(a) for a in activities]
        rows = [r for r in rows if r is not None]
        if not rows:
            return {"new_activities": 0}

        async with AsyncSessionFactory() as session:
            for row in rows:
                stmt = insert(StravaActivity).values(**row).on_conflict_do_nothing(
                    index_elements=["strava_activity_id"]
                )
                await session.execute(stmt)
            await session.commit()

        logger.info(f"[strava] {len(rows)} yeni aktivite kaydedildi")
        return {"new_activities": len(rows)}

    def _parse_activity(self, activity: dict) -> dict | None:
        activity_id = activity.get("id")
        start_date_raw = activity.get("start_date")
        if not activity_id or not start_date_raw:
            return None
        return {
            "strava_activity_id": str(activity_id),
            "name": activity.get("name"),
            "activity_type": activity.get("type"),
            "start_date": datetime.fromisoformat(start_date_raw.replace("Z", "+00:00")),
            "distance_m": activity.get("distance"),
            "moving_time_s": activity.get("moving_time"),
            "elapsed_time_s": activity.get("elapsed_time"),
            "total_elevation_gain_m": activity.get("total_elevation_gain"),
            "average_heartrate": activity.get("average_heartrate"),
            "max_heartrate": activity.get("max_heartrate"),
            "calories": activity.get("calories"),
        }
