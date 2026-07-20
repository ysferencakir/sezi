from typing import Any

from loguru import logger
from sqlalchemy.dialects.postgresql import insert

from core.base_module import BaseModule, Schedule
from core.config import settings
from core.database import AsyncSessionFactory
from modules.tefas import tefas_client
from modules.tefas.models import FundDay


class TefasModule(BaseModule):
    name = "tefas"
    description = "TEFAS izleme listesindeki fonların günlük fiyatı"

    def schedules(self) -> list[Schedule]:
        return [
            Schedule("daily_sync", "0 21 * * *", "run", "İzleme listesindeki fonların günlük fiyatını çek"),
        ]

    def _watchlist(self) -> list[str]:
        return [c.strip().upper() for c in settings.tefas_watchlist.split(",") if c.strip()]

    async def fetch(self) -> dict[str, Any]:
        rows: list[dict] = []
        for code in self._watchlist():
            rows.extend(await tefas_client.fetch_fund_history(code))
        return {"rows": rows}

    async def process(self, data: dict[str, Any]) -> dict[str, Any]:
        rows = data.get("rows", [])
        if not rows:
            return {}

        async with AsyncSessionFactory() as session:
            for row in rows:
                stmt = insert(FundDay).values(**row).on_conflict_do_update(
                    index_elements=["fund_code", "day"], set_=row
                )
                await session.execute(stmt)
            await session.commit()

        codes = sorted({r["fund_code"] for r in rows})
        logger.info(f"[tefas] {len(rows)} kayıt kaydedildi ({', '.join(codes)})")
        return {"rows_saved": len(rows)}
