from datetime import date
from typing import Any

from loguru import logger
from sqlalchemy import delete

from core.base_module import BaseModule, Schedule
from core.config import settings
from core.database import AsyncSessionFactory
from modules.energy import epias_client
from modules.energy.models import PowerOutage


class EnergyModule(BaseModule):
    name = "energy"
    description = "EPİAŞ üzerinden bugünün planlı/plansız elektrik kesintileri"

    def schedules(self) -> list[Schedule]:
        return [
            Schedule("daily_sync", "0 8 * * *", "run", "Bugünün kesinti bilgisini çek"),
        ]

    async def fetch(self) -> dict[str, Any]:
        if not settings.epias_username or not settings.epias_password:
            logger.warning("[energy] EPIAS_USERNAME/EPIAS_PASSWORD ayarlanmamış — atlanıyor")
            return {}

        today = date.today()
        planned = await epias_client.fetch_planned_outages(today)
        unplanned = await epias_client.fetch_unplanned_outages(today)
        return {"day": today, "planned": planned, "unplanned": unplanned}

    async def process(self, data: dict[str, Any]) -> dict[str, Any]:
        if not data:
            return {}

        day = data["day"]
        rows = [{"day": day, "outage_type": "planned", "raw": item} for item in data.get("planned", [])]
        rows += [{"day": day, "outage_type": "unplanned", "raw": item} for item in data.get("unplanned", [])]

        async with AsyncSessionFactory() as session:
            # Gün için tek sefer sync yapılıyor — o günün eski kayıtlarını silip yeniden yazmak
            # (upsert yerine) EPİAŞ'ın kesinti listesini güncelleyip iptal ettiği durumları yansıtır.
            await session.execute(delete(PowerOutage).where(PowerOutage.day == day))
            if rows:
                await session.execute(PowerOutage.__table__.insert(), rows)
            await session.commit()

        logger.info(f"[energy] {day} — {len(rows)} kesinti kaydı ({len(data.get('planned', []))} planlı, {len(data.get('unplanned', []))} plansız)")
        return {"outages_saved": len(rows)}
