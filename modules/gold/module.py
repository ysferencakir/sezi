from datetime import date
from typing import Any

from loguru import logger
from sqlalchemy.dialects.postgresql import insert

from core.base_module import BaseModule, Schedule
from core.config import settings
from core.database import AsyncSessionFactory
from modules.gold import altinapi_client
from modules.gold.models import GoldDay

# symbol -> (alış sütunu, satış sütunu)
_SYMBOL_COLUMNS = {
    "GRAM": ("gram_altin_alis", "gram_altin_satis"),
    "CEYREK_YENI": ("ceyrek_alis", "ceyrek_satis"),
    "YARIM_YENI": ("yarim_alis", "yarim_satis"),
    "TEK_YENI": ("tam_alis", "tam_satis"),
    "ATA_YENI": ("ata_alis", "ata_satis"),
}


class GoldModule(BaseModule):
    name = "gold"
    description = "altinapi.com üzerinden günlük altın (gram + sarrafiye) fiyat anlık görüntüsü"

    def schedules(self) -> list[Schedule]:
        return [
            Schedule("daily_sync", "0 20 * * *", "run", "Günün altın fiyat anlık görüntüsünü çek"),
        ]

    async def fetch(self) -> dict[str, Any]:
        if not settings.altinapi_key:
            logger.warning("[gold] ALTINAPI_KEY ayarlanmamış — atlanıyor")
            return {}

        altin = await altinapi_client.fetch_category("ALTIN")
        sarrafiye = await altinapi_client.fetch_category("SARRAFIYE")
        by_symbol = {row["symbol"]: row for row in [*altin, *sarrafiye] if "symbol" in row}
        return {"day": date.today(), "by_symbol": by_symbol}

    async def process(self, data: dict[str, Any]) -> dict[str, Any]:
        if not data or not data.get("by_symbol"):
            return {}

        by_symbol = data["by_symbol"]
        row: dict[str, Any] = {"day": data["day"], "raw": by_symbol}
        for symbol, (buy_col, sell_col) in _SYMBOL_COLUMNS.items():
            entry = by_symbol.get(symbol)
            row[buy_col] = entry.get("buy") if entry else None
            row[sell_col] = entry.get("sell") if entry else None

        async with AsyncSessionFactory() as session:
            stmt = insert(GoldDay).values(**row).on_conflict_do_update(
                index_elements=["day"], set_=row
            )
            await session.execute(stmt)
            await session.commit()

        logger.info(f"[gold] {row['day']} kaydedildi — gram altın satış {row.get('gram_altin_satis')}")
        return row
