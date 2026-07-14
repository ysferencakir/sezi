from typing import Any

from core.base_module import BaseModule, Schedule


class ContextModule(BaseModule):
    """Dış API'den veri çekmez. Kullanıcı verisi /api/context router'ı üzerinden gönderilir;
    hatırlatma metni digest modülünün evening_digest'i içinde yapılır."""

    name = "context"
    description = "Haftalık yansıma notu"

    def schedules(self) -> list[Schedule]:
        # Akşam hatırlatması artık digest modülünün evening_digest'i içinde.
        return []

    async def fetch(self) -> Any:
        return None

    async def process(self, data: Any) -> Any:
        return None
