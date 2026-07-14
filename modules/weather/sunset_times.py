from datetime import date, datetime

import httpx

_BASE_URL = "https://api.sunrise-sunset.org/json"

_EMPTY = {
    "sunrise": None, "sunset": None, "day_length_minutes": None,
    "solar_noon": None,
    "civil_twilight_begin": None, "civil_twilight_end": None,
    "nautical_twilight_begin": None, "nautical_twilight_end": None,
    "astronomical_twilight_begin": None, "astronomical_twilight_end": None,
}


async def fetch_sun_times(lat: float, lon: float, day: date) -> dict:
    """Belirtilen konum ve gün için gün doğumu/batımı ve alacakaranlık bilgisini çeker."""
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
        return dict(_EMPTY)

    results = data["results"]
    return {
        "sunrise": datetime.fromisoformat(results["sunrise"]),
        "sunset": datetime.fromisoformat(results["sunset"]),
        "day_length_minutes": int(results["day_length"] / 60),
        "solar_noon": datetime.fromisoformat(results["solar_noon"]),
        "civil_twilight_begin": datetime.fromisoformat(results["civil_twilight_begin"]),
        "civil_twilight_end": datetime.fromisoformat(results["civil_twilight_end"]),
        "nautical_twilight_begin": datetime.fromisoformat(results["nautical_twilight_begin"]),
        "nautical_twilight_end": datetime.fromisoformat(results["nautical_twilight_end"]),
        "astronomical_twilight_begin": datetime.fromisoformat(results["astronomical_twilight_begin"]),
        "astronomical_twilight_end": datetime.fromisoformat(results["astronomical_twilight_end"]),
    }
