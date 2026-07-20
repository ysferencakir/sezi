from datetime import date, datetime, timedelta, timezone
from typing import Any

import httpx

from core.config import settings

_TGT_URL = "https://cas.epias.com.tr/cas/v1/tickets"
_OUTAGE_BASE = "https://seffaflik.epias.com.tr/electricity-service"

# EPİAŞ TGT (Ticket Granting Ticket) 2 saat geçerli — her istekte yeniden almak
# yerine süreç içi (process-local) önbelleğe alınıyor. Uygulama yeniden başlarsa
# sıfırdan alınır; bu basit önbellek çoklu worker/process senaryosunda paylaşılmaz
# ama Sezi'nin tek-worker scheduler'ı için yeterli.
_tgt_cache: dict[str, Any] = {"token": None, "expires_at": None}


async def _get_tgt() -> str:
    cached = _tgt_cache["token"]
    if cached and _tgt_cache["expires_at"] > datetime.now(timezone.utc):
        return cached

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            _TGT_URL,
            data={"username": settings.epias_username, "password": settings.epias_password},
            headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "text/plain"},
            timeout=15.0,
        )
        resp.raise_for_status()
        tgt = resp.text.strip()

    _tgt_cache["token"] = tgt
    _tgt_cache["expires_at"] = datetime.now(timezone.utc) + timedelta(hours=1, minutes=50)
    return tgt


async def _post_outage(endpoint: str, day: date) -> list[dict[str, Any]]:
    tgt = await _get_tgt()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{_OUTAGE_BASE}/{endpoint}",
            json={
                "startDate": day.isoformat(),
                "endDate": day.isoformat(),
                "cityId": settings.epias_city_id or None,
            },
            headers={"TGT": tgt, "Content-Type": "application/json"},
            timeout=20.0,
        )
        resp.raise_for_status()
        body = resp.json()
        return body.get("items", []) if isinstance(body, dict) else body


async def fetch_planned_outages(day: date) -> list[dict[str, Any]]:
    return await _post_outage("planned-power-outage-data", day)


async def fetch_unplanned_outages(day: date) -> list[dict[str, Any]]:
    return await _post_outage("unplanned-power-outage-data", day)
