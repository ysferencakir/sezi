from datetime import date

import httpx

_BASE_URL = "https://date.nager.at/api/v3/PublicHolidays"

# Yıl başına bir kez çekilip bellekte tutulur — tatiller sık değişmez.
_cache: dict[int, dict[date, str]] = {}


async def _fetch_year(year: int, country: str) -> dict[date, str]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{_BASE_URL}/{year}/{country}")
        resp.raise_for_status()
        return {date.fromisoformat(item["date"]): item["localName"] for item in resp.json()}


async def get_holiday_name(day: date, country: str = "TR") -> str | None:
    """Belirtilen gün resmi tatilse yerel adını (localName), değilse None döner."""
    if day.year not in _cache:
        _cache[day.year] = await _fetch_year(day.year, country)
    return _cache[day.year].get(day)


async def is_public_holiday(day: date, country: str = "TR") -> bool:
    return await get_holiday_name(day, country) is not None
