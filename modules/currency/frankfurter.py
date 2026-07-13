from datetime import date

import httpx

_BASE_URL = "https://api.frankfurter.dev/v1"


async def fetch_rates(day: date, symbols: list[str], base: str = "USD") -> dict[str, float]:
    """Belirtilen gün için base para birimine göre kur değerlerini çeker."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{_BASE_URL}/{day.isoformat()}",
            params={"base": base, "symbols": ",".join(symbols)},
        )
        resp.raise_for_status()
        return resp.json().get("rates", {})
