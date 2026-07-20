from datetime import date
from typing import Any

import httpx

from core.config import settings

_URL = "https://evds2.tcmb.gov.tr/service/evds/series={series}&startDate={start}&endDate={end}&type=json"
# TCMB EVDS 05.04.2024'ten beri API key'i query param değil header olarak istiyor.
_SERIES = "TP.DK.USD.A-TP.DK.USD.S-TP.DK.EUR.A-TP.DK.EUR.S"


def _fmt(d: date) -> str:
    return d.strftime("%d-%m-%Y")


async def fetch_rates(day: date) -> dict[str, Any]:
    """Belirtilen gün için TCMB resmi USD/EUR alış-satış kurunu döner."""
    url = _URL.format(series=_SERIES, start=_fmt(day), end=_fmt(day))
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers={"key": settings.evds_api_key}, timeout=15.0)
        resp.raise_for_status()
        items = resp.json().get("items", [])
        return items[0] if items else {}
