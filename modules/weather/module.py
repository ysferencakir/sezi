from datetime import datetime, timedelta, timezone
from typing import Any

from loguru import logger
from sqlalchemy.dialects.postgresql import insert

from core.base_module import BaseModule, Schedule
from core.database import AsyncSessionFactory
from core.notifier import notifier
from modules.weather import location_service, open_meteo, open_meteo_air
from modules.weather.models import WeatherDay


class WeatherModule(BaseModule):
    name = "weather"
    description = "Telegram canlı konumuna göre günlük hava durumu (Open-Meteo)"

    def schedules(self) -> list[Schedule]:
        return [
            Schedule("daily_sync", "10 7 * * *", "run", "Dün'ün hava durumunu çek"),
        ]

    async def fetch(self) -> dict[str, Any]:
        location = await location_service.get_location()
        if location is None:
            logger.warning("[weather] Konum bilinmiyor — Telegram'da botla konum paylaş")
            return {}

        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).date()
        weather = await open_meteo.fetch_daily_weather(location.latitude, location.longitude, yesterday)
        air_quality = await open_meteo_air.fetch_daily_air_quality(location.latitude, location.longitude, yesterday)
        return {
            "day": yesterday,
            "latitude": location.latitude,
            "longitude": location.longitude,
            "weather": weather,
            "air_quality": air_quality,
        }

    async def process(self, data: dict[str, Any]) -> dict[str, Any]:
        if not data:
            return {}

        weather = data["weather"]
        air = data["air_quality"]
        values = {
            "day": data["day"],
            "latitude": data["latitude"],
            "longitude": data["longitude"],
            "temp_min": weather["temp_min"],
            "temp_max": weather["temp_max"],
            "precipitation_mm": weather["precipitation_mm"],
            "weather_code": weather["weather_code"],
            "condition": open_meteo.condition_from_code(weather["weather_code"]),
            "european_aqi": air["european_aqi"],
            "pm2_5": air["pm2_5"],
            "pm10": air["pm10"],
            "uv_index_max": air["uv_index_max"],
        }

        async with AsyncSessionFactory() as session:
            stmt = insert(WeatherDay).values(**values).on_conflict_do_update(
                index_elements=["day"], set_=values
            )
            await session.execute(stmt)
            await session.commit()

        logger.info(f"[weather] {values['day']} kaydedildi — {values['condition']}, {values['temp_min']}-{values['temp_max']}°C")
        return values
