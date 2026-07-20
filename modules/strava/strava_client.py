from typing import Any
from urllib.parse import urlencode

import httpx

from core.config import settings

_AUTH_URL = "https://www.strava.com/oauth/authorize"
_TOKEN_URL = "https://www.strava.com/oauth/token"
_API_BASE = "https://www.strava.com/api/v3"

SCOPES = ["activity:read_all"]


def build_auth_url(state: str = "") -> str:
    params = {
        "client_id": settings.strava_client_id,
        "redirect_uri": settings.strava_redirect_uri,
        "response_type": "code",
        "scope": ",".join(SCOPES),
        "approval_prompt": "auto",
        "state": state,
    }
    return f"{_AUTH_URL}?{urlencode(params)}"


async def exchange_code(code: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(_TOKEN_URL, data={
            "client_id": settings.strava_client_id,
            "client_secret": settings.strava_client_secret,
            "code": code,
            "grant_type": "authorization_code",
        })
        resp.raise_for_status()
        return resp.json()


async def refresh_access_token(refresh_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(_TOKEN_URL, data={
            "client_id": settings.strava_client_id,
            "client_secret": settings.strava_client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        })
        resp.raise_for_status()
        return resp.json()


async def fetch_activities(access_token: str, after_epoch: int, per_page: int = 50) -> list[dict[str, Any]]:
    """`after_epoch`'tan sonra başlayan aktiviteleri döner (Strava rate limit: 200 istek/15dk, 2.000/gün)."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{_API_BASE}/athlete/activities",
            params={"after": after_epoch, "per_page": per_page},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json()
