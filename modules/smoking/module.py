from typing import Any

from core.base_module import BaseModule, Schedule


class SmokingModule(BaseModule):
    """Dış API'den veri çekmez. Kullanıcı verisi Telegram bot /sigara komutu üzerinden gönderilir;
    akşam hatırlatması digest modülünün evening_digest'i içinde yapılır."""

    name = "smoking"
    description = "Günlük sigara sayısı hatırlatması"

    def schedules(self) -> list[Schedule]:
        # Akşam hatırlatması artık digest modülünün evening_digest'i içinde.
        return []

    async def fetch(self) -> Any:
        return None

    async def process(self, data: Any) -> Any:
        return None
