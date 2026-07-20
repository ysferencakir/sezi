from typing import Any

from core.base_module import BaseModule, Schedule


class WatchlogModule(BaseModule):
    """Dış API'den zamanlı veri çekmez. Kullanıcı verisi Telegram bot /izledim komutuyla
    gönderilir, TMDB ile zenginleştirilir (bkz. service.py)."""

    name = "watchlog"
    description = "Telegram /izledim komutuyla girilen dizi/film kayıtları (TMDB zenginleştirmeli)"

    def schedules(self) -> list[Schedule]:
        return []

    async def fetch(self) -> Any:
        return None

    async def process(self, data: Any) -> Any:
        return None
