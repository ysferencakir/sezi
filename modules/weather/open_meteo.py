from datetime import date

import httpx

_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

# WMO weather interpretation codes (kısaltılmış) — https://open-meteo.com/en/docs
_WEATHER_CODES = {
    0: "clear", 1: "mostly_clear", 2: "partly_cloudy", 3: "overcast",
    45: "fog", 48: "fog",
    51: "drizzle", 53: "drizzle", 55: "drizzle",
    61: "rain", 63: "rain", 65: "heavy_rain",
    71: "snow", 73: "snow", 75: "heavy_snow",
    80: "showers", 81: "showers", 82: "heavy_showers",
    95: "thunderstorm", 96: "thunderstorm", 99: "thunderstorm",
}


def condition_from_code(code: int | None) -> str | None:
    if code is None:
        return None
    return _WEATHER_CODES.get(code, "unknown")


_DAILY_FIELDS = (
    "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode,"
    "windspeed_10m_max,windgusts_10m_max,winddirection_10m_dominant,"
    "relative_humidity_2m_mean,surface_pressure_mean,cloudcover_mean,"
    "snowfall_sum,sunshine_duration"
)


async def fetch_daily_weather(lat: float, lon: float, day: date) -> dict:
    """Belirtilen konum ve gün için günlük hava durumu özetini çeker."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(_ARCHIVE_URL, params={
            "latitude": lat,
            "longitude": lon,
            "start_date": day.isoformat(),
            "end_date": day.isoformat(),
            "daily": _DAILY_FIELDS,
            "timezone": "UTC",
        })
        resp.raise_for_status()
        data = resp.json().get("daily", {})

    def first(key: str):
        values = data.get(key) or []
        return values[0] if values else None

    sunshine_seconds = first("sunshine_duration")

    return {
        "temp_max": first("temperature_2m_max"),
        "temp_min": first("temperature_2m_min"),
        "precipitation_mm": first("precipitation_sum"),
        "weather_code": first("weathercode"),
        "wind_speed_max": first("windspeed_10m_max"),
        "wind_gusts_max": first("windgusts_10m_max"),
        "wind_direction": first("winddirection_10m_dominant"),
        "humidity_mean": first("relative_humidity_2m_mean"),
        "pressure_mean": first("surface_pressure_mean"),
        "cloud_cover_mean": first("cloudcover_mean"),
        "snowfall_cm": first("snowfall_sum"),
        "sunshine_duration_minutes": int(sunshine_seconds / 60) if sunshine_seconds is not None else None,
    }
