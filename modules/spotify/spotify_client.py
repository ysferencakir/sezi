import base64
from datetime import datetime
from typing import Any

import httpx

from core.config import settings

_AUTH_URL = "https://accounts.spotify.com/authorize"
_TOKEN_URL = "https://accounts.spotify.com/api/token"
_API_BASE = "https://api.spotify.com/v1"

SCOPES = [
    "user-read-recently-played",
    "user-top-read",
]


def build_auth_url(state: str = "") -> str:
    params = {
        "client_id": settings.spotify_client_id,
        "redirect_uri": settings.spotify_redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "state": state,
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{_AUTH_URL}?{query}"


def _basic_auth_header() -> str:
    raw = f"{settings.spotify_client_id}:{settings.spotify_client_secret}".encode()
    return base64.b64encode(raw).decode()


async def exchange_code(code: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            _TOKEN_URL,
            data={
                "code": code,
                "redirect_uri": settings.spotify_redirect_uri,
                "grant_type": "authorization_code",
            },
            headers={"Authorization": f"Basic {_basic_auth_header()}"},
        )
        resp.raise_for_status()
        return resp.json()


async def refresh_access_token(refresh_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            _TOKEN_URL,
            data={
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
            headers={"Authorization": f"Basic {_basic_auth_header()}"},
        )
        resp.raise_for_status()
        return resp.json()


async def fetch_recently_played(access_token: str, after_ms: int, limit: int = 50) -> list[dict[str, Any]]:
    """`after_ms` epoch milisaniyesinden sonra çalınan parçaları döner (en fazla 50 — API limiti)."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{_API_BASE}/me/player/recently-played",
            params={"after": after_ms, "limit": limit},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json().get("items", [])


async def fetch_top_tracks(access_token: str, time_range: str = "short_term", limit: int = 10) -> list[dict[str, Any]]:
    """time_range: short_term (~4hf), medium_term (~6ay), long_term (tüm zamanlar)."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{_API_BASE}/me/top/tracks",
            params={"time_range": time_range, "limit": limit},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json().get("items", [])
