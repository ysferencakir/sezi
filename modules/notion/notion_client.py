from typing import Any

import httpx

from core.config import settings

_API_BASE = "https://api.notion.com/v1"
_VERSION = "2022-06-28"


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.notion_token}",
        "Notion-Version": _VERSION,
        "Content-Type": "application/json",
    }


async def find_page_by_title(database_id: str, title: str) -> str | None:
    """Title property'si (Sezi'de 'İsim') verilen değere eşit olan sayfayı arar, varsa id'sini döner."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{_API_BASE}/databases/{database_id}/query",
            headers=_headers(),
            json={"filter": {"property": "İsim", "title": {"equals": title}}},
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        return results[0]["id"] if results else None


async def create_page(database_id: str, properties: dict[str, Any]) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{_API_BASE}/pages",
            headers=_headers(),
            json={"parent": {"database_id": database_id}, "properties": properties},
        )
        resp.raise_for_status()
        return resp.json()


async def update_page(page_id: str, properties: dict[str, Any]) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.patch(
            f"{_API_BASE}/pages/{page_id}",
            headers=_headers(),
            json={"properties": properties},
        )
        resp.raise_for_status()
        return resp.json()
