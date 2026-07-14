from datetime import datetime, timedelta, timezone
from typing import Any

from loguru import logger
from sqlalchemy.dialects.postgresql import insert

from core.base_module import BaseModule, Schedule
from core.database import AsyncSessionFactory
from core.notifier import notifier
from modules.weather import location_service, open_meteo, open_meteo_air, sunset_times
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
        sun = await sunset_times.fetch_sun_times(location.latitude, location.longitude, yesterday)
        return {
            "day": yesterday,
            "latitude": location.latitude,
            "longitude": location.longitude,
            "weather": weather,
            "air_quality": air_quality,
            "sun": sun,
        }

    async def process(self, data: dict[str, Any]) -> dict[str, Any]:
        if not data:
            return {}

        weather = data["weather"]
        air = data["air_quality"]
        sun = data["sun"]
        values = {
            "day": data["day"],
            "latitude": data["latitude"],
            "longitude": data["longitude"],
            "temp_min": weather["temp_min"],
            "temp_max": weather["temp_max"],
            "precipitation_mm": weather["precipitation_mm"],
            "weather_code": weather["weather_code"],
            "condition": open_meteo.condition_from_code(weather["weather_code"]),
            "wind_speed_max": weather["wind_speed_max"],
            "wind_gusts_max": weather["wind_gusts_max"],
            "wind_direction": weather["wind_direction"],
            "humidity_mean": weather["humidity_mean"],
            "pressure_mean": weather["pressure_mean"],
            "cloud_cover_mean": weather["cloud_cover_mean"],
            "snowfall_cm": weather["snowfall_cm"],
            "sunshine_duration_minutes": weather["sunshine_duration_minutes"],
            "european_aqi": air["european_aqi"],
            "us_aqi": air["us_aqi"],
            "pm2_5": air["pm2_5"],
            "pm10": air["pm10"],
            "carbon_monoxide": air["carbon_monoxide"],
            "nitrogen_dioxide": air["nitrogen_dioxide"],
            "sulphur_dioxide": air["sulphur_dioxide"],
            "ozone": air["ozone"],
            "dust": air["dust"],
            "birch_pollen": air["birch_pollen"],
            "grass_pollen": air["grass_pollen"],
            "ragweed_pollen": air["ragweed_pollen"],
            "uv_index_max": air["uv_index_max"],
            "sunrise": sun["sunrise"],
            "sunset": sun["sunset"],
            "solar_noon": sun["solar_noon"],
            "civil_twilight_begin": sun["civil_twilight_begin"],
            "civil_twilight_end": sun["civil_twilight_end"],
            "nautical_twilight_begin": sun["nautical_twilight_begin"],
            "nautical_twilight_end": sun["nautical_twilight_end"],
            "astronomical_twilight_begin": sun["astronomical_twilight_begin"],
            "astronomical_twilight_end": sun["astronomical_twilight_end"],
            "day_length_minutes": sun["day_length_minutes"],
        }

        async with AsyncSessionFactory() as session:
            stmt = insert(WeatherDay).values(**values).on_conflict_do_update(
                index_elements=["day"], set_=values
            )
            await session.execute(stmt)
            await session.commit()

        logger.info(f"[weather] {values['day']} kaydedildi — {values['condition']}, {values['temp_min']}-{values['temp_max']}°C")
        return values
