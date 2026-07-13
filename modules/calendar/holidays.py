from datetime import date

import httpx

_BASE_URL = "https://date.nager.at/api/v3/PublicHolidays"

# Yıl başına bir kez çekilip bellekte tutulur — tatiller sık değişmez.
_cache: dict[int, set[date]] = {}


async def _fetch_year(year: int, country: str) -> set[date]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{_BASE_URL}/{year}/{country}")
        resp.raise_for_status()
        return {date.fromisoformat(item["date"]) for item in resp.json()}


async def is_public_holiday(day: date, country: str = "TR") -> bool:
    if day.year not in _cache:
        _cache[day.year] = await _fetch_year(day.year, country)
    return day in _cache[day.year]
