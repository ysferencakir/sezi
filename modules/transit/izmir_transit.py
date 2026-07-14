from typing import Any

import httpx

_BASE_URL = "https://openapi.izmir.bel.tr/api/iztek"
_CBS_BASE_URL = "https://openapi.izmir.bel.tr/api/ibb/cbs"


async def fetch_approaching_buses(durak_id: str) -> list[dict[str, Any]]:
    """Belirtilen durağa yaklaşan tüm otobüsleri (hat filtresi olmadan) döner."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{_BASE_URL}/duragayaklasanotobusler/{durak_id}")
        resp.raise_for_status()
        return resp.json() or []


async def fetch_line_approaching_buses(hat_id: str, durak_id: str) -> list[dict[str, Any]]:
    """Belirtilen hattın, belirtilen durağa yaklaşan otobüslerini döner."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{_BASE_URL}/hattinyaklasanotobusleri/{hat_id}/{durak_id}")
        resp.raise_for_status()
        return resp.json() or []


async def fetch_line_positions(hat_id: str) -> dict[str, Any]:
    """Belirtilen hatta ait tüm otobüslerin anlık konumunu döner."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{_BASE_URL}/hatotobuskonumlari/{hat_id}")
        resp.raise_for_status()
        return resp.json() or {}


async def fetch_nearby_stops(latitude: float, longitude: float) -> list[dict[str, Any]]:
    """Verilen konuma en yakın otobüs duraklarını (mesafeye göre sıralı) döner."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{_CBS_BASE_URL}/noktayayakinduraklar",
            params={
                "x": longitude,
                "y": latitude,
                "inCoordSys": "EPSG:4326",
                "outCoordSys": "EPSG:4326",
            },
        )
        resp.raise_for_status()
        return resp.json() or []
