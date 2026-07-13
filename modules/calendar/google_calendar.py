from datetime import datetime
from typing import Any

import httpx

_CALENDAR_BASE = "https://www.googleapis.com/calendar/v3/calendars/primary/events"

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
]


async def fetch_events(access_token: str, start: datetime, end: datetime) -> list[dict[str, Any]]:
    """Belirtilen aralıktaki takvim etkinliklerini çeker."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            _CALENDAR_BASE,
            params={
                "timeMin": start.isoformat(),
                "timeMax": end.isoformat(),
                "singleEvents": "true",
                "orderBy": "startTime",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json().get("items", [])
