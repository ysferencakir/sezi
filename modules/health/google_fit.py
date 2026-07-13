from datetime import datetime, timezone
from typing import Any

import httpx

from core.config import settings

_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_URL = "https://oauth2.googleapis.com/token"
_FIT_BASE = "https://www.googleapis.com/fitness/v1/users/me"

SCOPES = [
    "https://www.googleapis.com/auth/fitness.activity.read",
    "https://www.googleapis.com/auth/fitness.heart_rate.read",
    "https://www.googleapis.com/auth/fitness.sleep.read",
    "https://www.googleapis.com/auth/fitness.body.read",
    "https://www.googleapis.com/auth/fitness.location.read",  # com.google.distance.delta için gerekli
]

# Google Fit veri tipi sabitleri
_STEPS = "com.google.step_count.delta"
_CALORIES = "com.google.calories.expended"
_ACTIVE_MINUTES = "com.google.active_minutes"
_DISTANCE = "com.google.distance.delta"
_HEART_RATE = "com.google.heart_rate.bpm"
_SLEEP = "com.google.sleep.segment"

# Uyku evre kodları
SLEEP_STAGES = {1: "awake", 2: "sleep", 4: "light", 5: "deep", 6: "rem"}


def build_auth_url(scopes: list[str] | None = None, state: str = "") -> str:
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes or SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{_AUTH_URL}?{query}"


async def exchange_code(code: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(_TOKEN_URL, data={
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": settings.google_redirect_uri,
            "grant_type": "authorization_code",
        })
        resp.raise_for_status()
        return resp.json()


async def refresh_access_token(refresh_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.post(_TOKEN_URL, data={
            "refresh_token": refresh_token,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "grant_type": "refresh_token",
        })
        resp.raise_for_status()
        return resp.json()


def _to_nanos(dt: datetime) -> int:
    return int(dt.timestamp() * 1_000_000_000)


def _to_millis(dt: datetime) -> int:
    return int(dt.timestamp() * 1_000)


async def fetch_daily_aggregate(access_token: str, start: datetime, end: datetime) -> dict[str, Any]:
    """Gün içi adım, kalori, aktif süre, mesafe verisini çeker."""
    body = {
        "aggregateBy": [
            {"dataTypeName": _STEPS},
            {"dataTypeName": _CALORIES},
            {"dataTypeName": _ACTIVE_MINUTES},
            {"dataTypeName": _DISTANCE},
        ],
        "bucketByTime": {"durationMillis": 86_400_000},  # 1 gün
        "startTimeMillis": _to_millis(start),
        "endTimeMillis": _to_millis(end),
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{_FIT_BASE}/dataset:aggregate",
            json=body,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json()


async def fetch_heart_rate(access_token: str, start: datetime, end: datetime) -> dict[str, Any]:
    start_ns = _to_nanos(start)
    end_ns = _to_nanos(end)
    dataset_id = f"{start_ns}-{end_ns}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{_FIT_BASE}/dataSources/derived:{_HEART_RATE}:com.google.android.gms:merge_heart_rate_bpm/datasets/{dataset_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json()


async def fetch_sleep(access_token: str, start: datetime, end: datetime) -> dict[str, Any]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{_FIT_BASE}/sessions",
            params={
                "startTime": start.isoformat() + "Z",
                "endTime": end.isoformat() + "Z",
                "activityType": 72,  # sleep
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json()
