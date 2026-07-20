from typing import Any

import httpx

from core.config import settings

_API_BASE = "https://api.themoviedb.org/3"
POSTER_BASE = "https://image.tmdb.org/t/p/w342"


async def search(query: str) -> dict[str, Any] | None:
    """En alakalı film/dizi sonucunu döner (TMDB'nin kendi relevance sıralamasına göre ilk sonuç).
    Kişi (person) sonuçları filtrelenir. Eşleşme yoksa veya key ayarlanmamışsa None döner."""
    if not settings.tmdb_api_key:
        return None

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{_API_BASE}/search/multi",
            params={"api_key": settings.tmdb_api_key, "query": query, "language": "tr-TR"},
            timeout=15.0,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])

    for item in results:
        media_type = item.get("media_type")
        if media_type not in ("movie", "tv"):
            continue
        return {
            "tmdb_id": item.get("id"),
            "media_type": media_type,
            "title": item.get("title") or item.get("name"),
            "overview": item.get("overview"),
            "poster_path": item.get("poster_path"),
            "release_date": item.get("release_date") or item.get("first_air_date"),
        }
    return None
