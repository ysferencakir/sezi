from typing import Any

from core.base_module import BaseModule, Schedule
from core.notifier import notifier


class SmokingModule(BaseModule):
    """Dış API'den veri çekmez — akşam hatırlatması gönderir.
    Kullanıcı verisi Telegram bot /sigara komutu üzerinden gönderilir."""

    name = "smoking"
    description = "Günlük sigara sayısı hatırlatması"

    def schedules(self) -> list[Schedule]:
        return [
            Schedule("evening_reminder", "45 22 * * *", "remind", "Her akşam 22:45 (TR) sigara sayısı hatırlatması"),
        ]

    async def fetch(self) -> Any:
        return None

    async def process(self, data: Any) -> Any:
        return None

    async def remind(self) -> None:
        await notifier.send("Bugün kaç sigara içtin? Bota /sigara yaz.", title="Günlük Kayıt")
