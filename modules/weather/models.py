from datetime import datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class UserLocation(Base):
    """Latest known user location, updated via Telegram location sharing."""
    __tablename__ = "user_location"

    id: Mapped[int] = mapped_column(primary_key=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class WeatherDay(Base):
    """Daily weather summary from Open-Meteo for the last known location."""
    __tablename__ = "weather_days"

    id: Mapped[int] = mapped_column(primary_key=True)
    day: Mapped[datetime] = mapped_column(Date, unique=True, index=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    temp_min: Mapped[float | None] = mapped_column(Float, default=None)
    temp_max: Mapped[float | None] = mapped_column(Float, default=None)
    precipitation_mm: Mapped[float | None] = mapped_column(Float, default=None)
    weather_code: Mapped[int | None] = mapped_column(Integer, default=None)
    condition: Mapped[str | None] = mapped_column(String(50), default=None)
    european_aqi: Mapped[int | None] = mapped_column(Integer, default=None)
    us_aqi: Mapped[int | None] = mapped_column(Integer, default=None)
    pm2_5: Mapped[float | None] = mapped_column(Float, default=None)
    pm10: Mapped[float | None] = mapped_column(Float, default=None)
    carbon_monoxide: Mapped[float | None] = mapped_column(Float, default=None)
    nitrogen_dioxide: Mapped[float | None] = mapped_column(Float, default=None)
    sulphur_dioxide: Mapped[float | None] = mapped_column(Float, default=None)
    ozone: Mapped[float | None] = mapped_column(Float, default=None)
    dust: Mapped[float | None] = mapped_column(Float, default=None)
    birch_pollen: Mapped[float | None] = mapped_column(Float, default=None)
    grass_pollen: Mapped[float | None] = mapped_column(Float, default=None)
    ragweed_pollen: Mapped[float | None] = mapped_column(Float, default=None)
    uv_index_max: Mapped[float | None] = mapped_column(Float, default=None)
    wind_speed_max: Mapped[float | None] = mapped_column(Float, default=None)
    wind_gusts_max: Mapped[float | None] = mapped_column(Float, default=None)
    wind_direction: Mapped[int | None] = mapped_column(Integer, default=None)
    humidity_mean: Mapped[float | None] = mapped_column(Float, default=None)
    pressure_mean: Mapped[float | None] = mapped_column(Float, default=None)
    cloud_cover_mean: Mapped[float | None] = mapped_column(Float, default=None)
    snowfall_cm: Mapped[float | None] = mapped_column(Float, default=None)
    sunshine_duration_minutes: Mapped[int | None] = mapped_column(Integer, default=None)
    sunrise: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    sunset: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    solar_noon: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    civil_twilight_begin: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    civil_twilight_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    nautical_twilight_begin: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    nautical_twilight_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    astronomical_twilight_begin: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    astronomical_twilight_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    day_length_minutes: Mapped[int | None] = mapped_column(Integer, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
