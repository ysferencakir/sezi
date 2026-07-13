from datetime import date, timedelta
from typing import Any

from core.base_module import BaseModule, Schedule
from core.notifier import notifier


class ContextModule(BaseModule):
    """Dış API'den veri çekmez — sadece haftalık yansıma hatırlatması gönderir.
    Kullanıcı verisi /api/context router'ı üzerinden gönderilir."""

    name = "context"
    description = "Haftalık yansıma notu hatırlatması"

    def schedules(self) -> list[Schedule]:
        return [
            Schedule("evening_reminder", "45 22 * * *", "remind", "Her akşam 22:45 (TR) context hatırlatması"),
        ]

    async def fetch(self) -> Any:
        return None

    async def process(self, data: Any) -> Any:
        return None

    async def remind(self) -> None:
        week_start = date.today() - timedelta(days=date.today().weekday())
        msg = (
            f"Bu hafta ({week_start}) nasıl geçti?\n"
            f"Bota /context yaz, birkaç dakikanı ayırıp not düş."
        )
        await notifier.send(msg, title="Haftalık Yansıma")
