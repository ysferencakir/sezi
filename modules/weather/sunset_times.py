from datetime import date, datetime

import httpx

_BASE_URL = "https://api.sunrise-sunset.org/json"


async def fetch_sun_times(lat: float, lon: float, day: date) -> dict:
    """Belirtilen konum ve gün için gün doğumu/batımı bilgisini çeker."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(_BASE_URL, params={
            "lat": lat,
            "lng": lon,
            "date": day.isoformat(),
            "formatted": 0,
        })
        resp.raise_for_status()
        data = resp.json()

    if data.get("status") != "OK":
        return {"sunrise": None, "sunset": None, "day_length_minutes": None}

    results = data["results"]
    return {
        "sunrise": datetime.fromisoformat(results["sunrise"]),
        "sunset": datetime.fromisoformat(results["sunset"]),
        "day_length_minutes": int(results["day_length"] / 60),
    }
