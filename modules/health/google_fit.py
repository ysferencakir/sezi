from datetime import datetime, timezone
from typing import Any

import httpx
from loguru import logger

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
    "https://www.googleapis.com/auth/fitness.nutrition.read",  # nutrition + hydration
    "https://www.googleapis.com/auth/fitness.blood_pressure.read",
    "https://www.googleapis.com/auth/fitness.blood_glucose.read",
    "https://www.googleapis.com/auth/fitness.oxygen_saturation.read",
]

# Google Fit veri tipi sabitleri
_STEPS = "com.google.step_count.delta"
_CALORIES = "com.google.calories.expended"
_ACTIVE_MINUTES = "com.google.active_minutes"
_DISTANCE = "com.google.distance.delta"
_HEART_RATE = "com.google.heart_rate.bpm"
_SLEEP = "com.google.sleep.segment"
_WEIGHT = "com.google.weight"
_HEIGHT = "com.google.height"
_BODY_FAT = "com.google.body.fat.percentage"
_NUTRITION = "com.google.nutrition"
_BLOOD_PRESSURE = "com.google.blood_pressure"
_BLOOD_GLUCOSE = "com.google.blood_glucose"
_OXYGEN_SATURATION = "com.google.oxygen_saturation"
_HYDRATION = "com.google.hydration"

# Delta tipler günlük toplanır (sum), anlık ölçümler günün son değeri alınır (last).
_DELTA_TYPES = {_STEPS, _CALORIES, _ACTIVE_MINUTES, _DISTANCE, _NUTRITION, _HYDRATION}
_INSTANT_TYPES = {_WEIGHT, _HEIGHT, _BODY_FAT, _BLOOD_PRESSURE, _BLOOD_GLUCOSE, _OXYGEN_SATURATION}

# Uyku evre kodları (com.google.sleep.segment intVal)
SLEEP_STAGES = {1: "awake", 2: "sleep", 3: "out_of_bed", 4: "light", 5: "deep", 6: "rem"}

# Sık görülen Google Fit aktivite tipi kodları (sessions.activityType)
ACTIVITY_TYPES = {
    1: "biking", 7: "walking", 8: "running", 9: "aerobics", 10: "badminton",
    11: "baseball", 12: "basketball", 13: "biathlon", 14: "handbiking",
    17: "bowling", 18: "boxing", 19: "calisthenics", 20: "circuit_training",
    21: "cricket", 24: "dancing", 27: "elliptical", 28: "fencing",
    32: "football_american", 33: "football_australian", 34: "football_soccer",
    35: "golf", 36: "gymnastics", 37: "handball", 38: "hiking",
    39: "hockey", 41: "horseback_riding", 44: "hunting", 46: "ice_skating",
    47: "jumping_rope", 48: "kayaking", 49: "kettlebell_training",
    52: "martial_arts", 53: "meditation", 55: "mountain_biking",
    56: "paddling", 57: "polo", 59: "racquetball", 61: "rock_climbing",
    62: "rowing", 63: "rowing_machine", 64: "rugby", 65: "jogging",
    66: "running_treadmill", 68: "sailing", 69: "scuba_diving",
    70: "skateboarding", 71: "skating", 72: "sleep", 73: "sledding",
    74: "skiing", 79: "snowboarding", 80: "snowmobile", 81: "snowshoeing",
    82: "squash", 83: "stair_climbing", 84: "stair_climbing_machine",
    85: "stand_up_paddleboarding", 87: "strength_training", 88: "surfing",
    89: "swimming", 90: "swimming_pool", 91: "swimming_open_water",
    92: "table_tennis", 93: "team_sports", 94: "tennis", 95: "treadmill",
    96: "volleyball", 97: "volleyball_beach", 98: "volleyball_indoor",
    99: "wheelchair", 100: "windsurfing", 101: "wrestling", 102: "yoga",
    103: "zumba", 108: "crossfit", 109: "hiit", 112: "guided_breathing",
    113: "mixed_martial_arts", 116: "walking_treadmill", 119: "weightlifting",
}


def activity_type_name(code: int) -> str:
    return ACTIVITY_TYPES.get(code, f"type_{code}")


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


# Fit API tek aggregate isteğindeki TÜM dataType'ları birlikte doğruluyor — istenen scope'lardan
# biri bile eksikse (örn. nutrition.read verilmemişse) 403 dönüp isteğin tamamını reddediyor.
# Bu yüzden scope gruplarına göre ayrı isteklere bölünüyor; bir grup 403 verirse diğerleri etkilenmez.
_CORE_TYPES = [_STEPS, _CALORIES, _ACTIVE_MINUTES, _DISTANCE, _WEIGHT, _HEIGHT, _BODY_FAT]
_SCOPED_TYPE_GROUPS = [
    [_NUTRITION, _HYDRATION],
    [_BLOOD_PRESSURE],
    [_BLOOD_GLUCOSE],
    [_OXYGEN_SATURATION],
]


async def _aggregate_request(client: httpx.AsyncClient, access_token: str, types: list[str], start: datetime, end: datetime) -> dict[str, Any]:
    body = {
        "aggregateBy": [{"dataTypeName": t} for t in types],
        "bucketByTime": {"durationMillis": 86_400_000},  # 1 gün
        "startTimeMillis": _to_millis(start),
        "endTimeMillis": _to_millis(end),
    }
    resp = await client.post(
        f"{_FIT_BASE}/dataset:aggregate",
        json=body,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    resp.raise_for_status()
    return resp.json()


async def fetch_daily_aggregate(access_token: str, start: datetime, end: datetime) -> dict[str, Any]:
    """Gün içi adım/kalori/aktif süre/mesafe + vücut ölçümleri/beslenme/diğer sağlık verisini çeker.

    Kullanıcı bazı veri tiplerini hiç kaydetmiyor ya da ilgili granular scope'u vermemiş olabilir
    (örn. tansiyon) — bu durumda o grup sessizce atlanır, diğer gruplar etkilenmez.
    """
    merged_buckets: dict[str, Any] = {"bucket": []}

    async with httpx.AsyncClient() as client:
        core = await _aggregate_request(client, access_token, _CORE_TYPES, start, end)
        merged_buckets["bucket"] = core.get("bucket", [])

        for group in _SCOPED_TYPE_GROUPS:
            try:
                extra = await _aggregate_request(client, access_token, group, start, end)
            except httpx.HTTPStatusError as exc:
                logger.warning(f"[health] {group} çekilemedi (scope eksik olabilir): {exc}")
                continue
            for i, bucket in enumerate(extra.get("bucket", [])):
                if i < len(merged_buckets["bucket"]):
                    merged_buckets["bucket"][i]["dataset"].extend(bucket.get("dataset", []))
                else:
                    merged_buckets["bucket"].append(bucket)

    return merged_buckets


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
                "startTime": start.isoformat(),
                "endTime": end.isoformat(),
                "activityType": 72,  # sleep
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json()


async def fetch_sleep_stages(access_token: str, start: datetime, end: datetime) -> dict[str, Any]:
    """Uyku evre segmentlerini (awake/light/deep/rem) çeker — session'dan daha ayrıntılı.
    Kullanıcının cihazı evre verisi üretmiyorsa boş point listesi döner."""
    start_ns = _to_nanos(start)
    end_ns = _to_nanos(end)
    dataset_id = f"{start_ns}-{end_ns}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{_FIT_BASE}/dataSources/derived:{_SLEEP}:com.google.android.gms:merged/datasets/{dataset_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if resp.status_code == 404:
            return {"point": []}
        resp.raise_for_status()
        return resp.json()


async def fetch_sessions(access_token: str, start: datetime, end: datetime) -> dict[str, Any]:
    """Uyku dahil tüm session'ları (antrenman/aktivite) çeker — activityType filtresiz."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{_FIT_BASE}/sessions",
            params={"startTime": start.isoformat(), "endTime": end.isoformat()},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json()
