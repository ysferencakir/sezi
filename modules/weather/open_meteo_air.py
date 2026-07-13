from datetime import date

import httpx

_AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


async def fetch_daily_air_quality(lat: float, lon: float, day: date) -> dict:
    """Belirtilen konum ve gün için saatlik veriden günlük hava kalitesi özetini (max) çıkarır.

    Open-Meteo'nun air-quality API'si "daily" toplulaştırma parametresini
    desteklemiyor (yalnızca "hourly" kabul ediyor) — bu yüzden saatlik veri
    çekilip günün maksimum değerleri burada hesaplanıyor.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(_AIR_QUALITY_URL, params={
            "latitude": lat,
            "longitude": lon,
            "start_date": day.isoformat(),
            "end_date": day.isoformat(),
            "hourly": "european_aqi,pm2_5,pm10,uv_index",
            "timezone": "UTC",
        })
        resp.raise_for_status()
        data = resp.json().get("hourly", {})

    def day_max(key: str):
        values = [v for v in (data.get(key) or []) if v is not None]
        return max(values) if values else None

    aqi = day_max("european_aqi")
    return {
        "european_aqi": int(round(aqi)) if aqi is not None else None,
        "pm2_5": day_max("pm2_5"),
        "pm10": day_max("pm10"),
        "uv_index_max": day_max("uv_index"),
    }
