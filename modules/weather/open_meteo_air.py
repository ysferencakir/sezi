from datetime import date

import httpx

_AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

_HOURLY_FIELDS = (
    "european_aqi,us_aqi,pm2_5,pm10,uv_index,"
    "carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone,dust,"
    "birch_pollen,grass_pollen,ragweed_pollen"
)


async def fetch_daily_air_quality(lat: float, lon: float, day: date) -> dict:
    """Belirtilen konum ve gün için saatlik veriden günlük hava kalitesi özetini (max) çıkarır.

    Open-Meteo'nun air-quality API'si "daily" toplulaştırma parametresini
    desteklemiyor (yalnızca "hourly" kabul ediyor) — bu yüzden saatlik veri
    çekilip günün maksimum değerleri burada hesaplanıyor. Polen verisi sadece
    Avrupa/Kuzey Amerika kapsamında mevcut — kapsam dışı konumlarda None döner.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(_AIR_QUALITY_URL, params={
            "latitude": lat,
            "longitude": lon,
            "start_date": day.isoformat(),
            "end_date": day.isoformat(),
            "hourly": _HOURLY_FIELDS,
            "timezone": "UTC",
        })
        resp.raise_for_status()
        data = resp.json().get("hourly", {})

    def day_max(key: str):
        values = [v for v in (data.get(key) or []) if v is not None]
        return max(values) if values else None

    aqi = day_max("european_aqi")
    us_aqi = day_max("us_aqi")
    return {
        "european_aqi": int(round(aqi)) if aqi is not None else None,
        "us_aqi": int(round(us_aqi)) if us_aqi is not None else None,
        "pm2_5": day_max("pm2_5"),
        "pm10": day_max("pm10"),
        "uv_index_max": day_max("uv_index"),
        "carbon_monoxide": day_max("carbon_monoxide"),
        "nitrogen_dioxide": day_max("nitrogen_dioxide"),
        "sulphur_dioxide": day_max("sulphur_dioxide"),
        "ozone": day_max("ozone"),
        "dust": day_max("dust"),
        "birch_pollen": day_max("birch_pollen"),
        "grass_pollen": day_max("grass_pollen"),
        "ragweed_pollen": day_max("ragweed_pollen"),
    }
