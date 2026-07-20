from email.utils import parsedate_to_datetime
from typing import Any

from loguru import logger
from sqlalchemy.dialects.postgresql import insert

from core.base_module import BaseModule, Schedule
from core.config import settings
from core.database import AsyncSessionFactory
from modules.events import etkinlik_client
from modules.events.models import EventItem


class EventsModule(BaseModule):
    name = "events"
    description = "Etkinlik.io RSS üzerinden güncel etkinlik akışı"

    def schedules(self) -> list[Schedule]:
        return [
            Schedule("daily_sync", "0 9 * * *", "run", "Güncel etkinlik akışını çek"),
        ]

    async def fetch(self) -> dict[str, Any]:
        items = await etkinlik_client.fetch_feed()
        city = settings.etkinlik_city.strip().lower()
        if city:
            items = [
                i for i in items
                if city in i["title"].lower() or city in i["description"].lower()
            ]
        return {"items": items}

    async def process(self, data: dict[str, Any]) -> dict[str, Any]:
        items = data.get("items", [])
        if not items:
            return {}

        async with AsyncSessionFactory() as session:
            new_count = 0
            for item in items:
                published_at = None
                if item["pub_date"]:
                    try:
                        published_at = parsedate_to_datetime(item["pub_date"])
                    except (TypeError, ValueError):
                        published_at = None

                stmt = insert(EventItem).values(
                    link=item["link"],
                    title=item["title"],
                    category=item["category"] or None,
                    description=item["description"] or None,
                    published_at=published_at,
                ).on_conflict_do_nothing(index_elements=["link"])
                result = await session.execute(stmt)
                if result.rowcount:
                    new_count += 1
            await session.commit()

        logger.info(f"[events] {new_count} yeni etkinlik kaydedildi ({len(items)} toplam)")
        return {"new_events": new_count}
