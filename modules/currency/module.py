from datetime import datetime, timedelta, timezone
from typing import Any

from loguru import logger
from sqlalchemy.dialects.postgresql import insert

from core.base_module import BaseModule, Schedule
from core.database import AsyncSessionFactory
from modules.currency import frankfurter
from modules.currency.models import CurrencyDay


class CurrencyModule(BaseModule):
    name = "currency"
    description = "Frankfurter (ECB) üzerinden günlük USD/EUR -> TRY kurları"

    def schedules(self) -> list[Schedule]:
        return [
            Schedule("daily_sync", "20 7 * * *", "run", "Dün'ün döviz kurlarını çek"),
        ]

    async def fetch(self) -> dict[str, Any]:
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).date()
        usd_rates = await frankfurter.fetch_rates(yesterday, symbols=["TRY"], base="USD")
        eur_rates = await frankfurter.fetch_rates(yesterday, symbols=["TRY"], base="EUR")
        gbp_rates = await frankfurter.fetch_rates(yesterday, symbols=["TRY"], base="GBP")
        chf_rates = await frankfurter.fetch_rates(yesterday, symbols=["TRY"], base="CHF")
        return {
            "day": yesterday,
            "usd_try": usd_rates.get("TRY"),
            "eur_try": eur_rates.get("TRY"),
            "gbp_try": gbp_rates.get("TRY"),
            "chf_try": chf_rates.get("TRY"),
        }

    async def process(self, data: dict[str, Any]) -> dict[str, Any]:
        if not data:
            return {}

        async with AsyncSessionFactory() as session:
            stmt = insert(CurrencyDay).values(**data).on_conflict_do_update(
                index_elements=["day"], set_=data
            )
            await session.execute(stmt)
            await session.commit()

        logger.info(f"[currency] {data['day']} kaydedildi — USD/TRY {data['usd_try']}, EUR/TRY {data['eur_try']}")
        return data
