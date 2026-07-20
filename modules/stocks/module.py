from typing import Any

from loguru import logger
from sqlalchemy.dialects.postgresql import insert

from core.base_module import BaseModule, Schedule
from core.config import settings
from core.database import AsyncSessionFactory
from modules.stocks import yahoo_finance
from modules.stocks.models import StockDay


class StocksModule(BaseModule):
    name = "stocks"
    description = "Yahoo Finance üzerinden BIST hisse/endeks günlük kapanışları"

    def schedules(self) -> list[Schedule]:
        return [
            Schedule("daily_sync", "30 20 * * *", "run", "İzleme listesindeki sembollerin günlük kapanışını çek"),
        ]

    def _watchlist(self) -> list[str]:
        return [s.strip() for s in settings.stocks_watchlist.split(",") if s.strip()]

    async def fetch(self) -> dict[str, Any]:
        bars: dict[str, dict] = {}
        for symbol in self._watchlist():
            bar = await yahoo_finance.fetch_last_daily_bar(symbol)
            if bar:
                bars[symbol] = bar
        return {"bars": bars}

    async def process(self, data: dict[str, Any]) -> dict[str, Any]:
        bars = data.get("bars", {})
        if not bars:
            return {}

        async with AsyncSessionFactory() as session:
            for symbol, bar in bars.items():
                row = {"symbol": symbol, **bar}
                stmt = insert(StockDay).values(**row).on_conflict_do_update(
                    index_elements=["symbol", "day"], set_=row
                )
                await session.execute(stmt)
            await session.commit()

        logger.info(f"[stocks] {len(bars)} sembol kaydedildi: {', '.join(bars)}")
        return {"symbols_updated": len(bars)}
