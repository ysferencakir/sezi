from typing import Any

import httpx

from core.config import settings

_API_BASE = "https://altinapi.com/api/v1"


async def fetch_category(category: str) -> list[dict[str, Any]]:
    """`category`: ALTIN, DOVIZ, MADEN veya SARRAFIYE. Her sembol için {symbol, buy, sell, updatedAt} döner."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{_API_BASE}/prices/category/{category}",
            headers={"X-API-Key": settings.altinapi_key},
            timeout=15.0,
        )
        resp.raise_for_status()
        body = resp.json()
        return body.get("result", []) if isinstance(body, dict) else body
