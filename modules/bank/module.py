from datetime import date
from typing import Any

from loguru import logger
from sqlalchemy.dialects.postgresql import insert

from core.base_module import BaseModule, Schedule
from core.database import AsyncSessionFactory
from modules.bank import kobakus_client
from modules.bank.models import BankAccountSnapshot


class BankModule(BaseModule):
    name = "bank"
    description = "Kobaküs Open Banking üzerinden çok bankalı hesap bakiyesi anlık görüntüsü"

    def schedules(self) -> list[Schedule]:
        return [
            Schedule("daily_sync", "0 9 * * *", "run", "Bağlı banka hesaplarının günlük bakiyesini çek"),
        ]

    async def fetch(self) -> dict[str, Any]:
        accounts = await kobakus_client.fetch_accounts()
        return {"day": date.today(), "accounts": accounts}

    async def process(self, data: dict[str, Any]) -> dict[str, Any]:
        accounts = data.get("accounts", [])
        if not accounts:
            return {}

        day = data["day"]
        async with AsyncSessionFactory() as session:
            for account in accounts:
                iban = account.get("Iban")
                if not iban:
                    continue
                row = {
                    "day": day,
                    "iban": iban,
                    "bank_name": account.get("BankName"),
                    "balance": account.get("Balance"),
                    "currency": account.get("Currency"),
                }
                stmt = insert(BankAccountSnapshot).values(**row).on_conflict_do_update(
                    index_elements=["day", "iban"], set_=row
                )
                await session.execute(stmt)
            await session.commit()

        logger.info(f"[bank] {day} — {len(accounts)} hesap kaydedildi")
        return {"accounts_saved": len(accounts)}
