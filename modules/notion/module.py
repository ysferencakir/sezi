from datetime import date
from typing import Any

from loguru import logger
from sqlalchemy import select

from core.base_module import BaseModule, Schedule
from core.config import settings
from core.database import AsyncSessionFactory
from modules.calendar.models import CalendarDay
from modules.health.models import HealthDay
from modules.notion import notion_client
from modules.smoking.models import SmokingDay
from modules.weather.models import WeatherDay


class NotionModule(BaseModule):
    """Sezi'nin günlük özetini Notion'da kullanıcının paylaştığı bir database'e yazar.
    Notion'dan veri OKUMAZ — sadece hedef (write-only)."""

    name = "notion"
    description = "Günlük özeti Notion database'ine yazar"

    def schedules(self) -> list[Schedule]:
        return [
            Schedule("daily_sync", "0 23 * * *", "run", "Bugünün özetini Notion'a yaz"),
        ]

    async def fetch(self) -> dict[str, Any]:
        if not settings.notion_token or not settings.notion_database_id:
            logger.warning("[notion] NOTION_TOKEN veya NOTION_DATABASE_ID ayarlanmamış — atlanıyor")
            return {}

        today = date.today()
        async with AsyncSessionFactory() as session:
            health = (
                await session.execute(select(HealthDay).order_by(HealthDay.day.desc()).limit(1))
            ).scalar_one_or_none()
            calendar = (
                await session.execute(select(CalendarDay).order_by(CalendarDay.day.desc()).limit(1))
            ).scalar_one_or_none()
            weather = (
                await session.execute(select(WeatherDay).order_by(WeatherDay.day.desc()).limit(1))
            ).scalar_one_or_none()
            smoking = (
                await session.execute(select(SmokingDay).where(SmokingDay.day == today))
            ).scalar_one_or_none()

        return {
            "day": today,
            "steps": health.steps if health else None,
            "meeting_count": calendar.meeting_count if calendar else None,
            "weather": f"{weather.temp_min:.0f}-{weather.temp_max:.0f}°C {weather.condition}" if weather else None,
            "smoking_count": smoking.count if smoking else 0,
        }

    async def process(self, data: dict[str, Any]) -> dict[str, Any]:
        if not data:
            return {}

        day_str = data["day"].isoformat()
        properties: dict[str, Any] = {
            "İsim": {"title": [{"text": {"content": day_str}}]},
            "Tarih": {"date": {"start": day_str}},
            "Sigara": {"number": data["smoking_count"]},
        }
        if data["steps"] is not None:
            properties["Adım"] = {"number": data["steps"]}
        if data["meeting_count"] is not None:
            properties["Toplantı"] = {"number": data["meeting_count"]}
        if data["weather"] is not None:
            properties["Hava"] = {"rich_text": [{"text": {"content": data["weather"]}}]}

        existing_id = await notion_client.find_page_by_title(settings.notion_database_id, day_str)
        if existing_id:
            await notion_client.update_page(existing_id, properties)
        else:
            await notion_client.create_page(settings.notion_database_id, properties)

        logger.info(f"[notion] {day_str} Notion'a yazıldı")
        return {"day": day_str}
