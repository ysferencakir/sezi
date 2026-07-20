from datetime import datetime, timedelta, timezone
from typing import Any

from loguru import logger
from sqlalchemy.dialects.postgresql import insert

from core.base_module import BaseModule, Schedule
from core.config import settings
from core.database import AsyncSessionFactory
from modules.evds import evds_client
from modules.evds.models import EvdsDay


def _to_float(value: Any) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


class EvdsModule(BaseModule):
    name = "evds"
    description = "TCMB EVDS üzerinden resmi günlük USD/EUR alış-satış kuru"

    def schedules(self) -> list[Schedule]:
        return [
            Schedule("daily_sync", "30 7 * * *", "run", "Dün'ün resmi TCMB kurunu çek"),
        ]

    async def fetch(self) -> dict[str, Any]:
        if not settings.evds_api_key:
            logger.warning("[evds] EVDS_API_KEY ayarlanmamış — atlanıyor")
            return {}

        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).date()
        item = await evds_client.fetch_rates(yesterday)
        return {"day": yesterday, "item": item}

    async def process(self, data: dict[str, Any]) -> dict[str, Any]:
        item = data.get("item")
        if not item:
            return {}

        row = {
            "day": data["day"],
            "usd_alis": _to_float(item.get("TP_DK_USD_A")),
            "usd_satis": _to_float(item.get("TP_DK_USD_S")),
            "eur_alis": _to_float(item.get("TP_DK_EUR_A")),
            "eur_satis": _to_float(item.get("TP_DK_EUR_S")),
        }

        async with AsyncSessionFactory() as session:
            stmt = insert(EvdsDay).values(**row).on_conflict_do_update(
                index_elements=["day"], set_=row
            )
            await session.execute(stmt)
            await session.commit()

        logger.info(f"[evds] {row['day']} kaydedildi — USD satış {row['usd_satis']}")
        return row
