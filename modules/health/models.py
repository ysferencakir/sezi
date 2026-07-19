from datetime import datetime
from sqlalchemy import JSON, Date, DateTime, Float, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base


class OAuthToken(Base):
    """OAuth 2.0 token storage for external APIs."""
    __tablename__ = "oauth_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(50), unique=True, index=True)  # e.g. "google"
    access_token: Mapped[str] = mapped_column(String(2048))
    refresh_token: Mapped[str] = mapped_column(String(2048))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class HealthDay(Base):
    """Daily health aggregate from Google Fit or Health Connect."""
    __tablename__ = "health_days"

    id: Mapped[int] = mapped_column(primary_key=True)
    day: Mapped[datetime] = mapped_column(Date, unique=True, index=True)
    steps: Mapped[int] = mapped_column(Integer, default=0)
    calories: Mapped[float] = mapped_column(Float, default=0.0)
    active_minutes: Mapped[int] = mapped_column(Integer, default=0)
    distance_meters: Mapped[float] = mapped_column(Float, default=0.0)
    # Vücut ölçümleri (son ölçülen değer o gün için)
    weight_kg: Mapped[float | None] = mapped_column(Float, default=None)
    height_cm: Mapped[float | None] = mapped_column(Float, default=None)
    body_fat_percent: Mapped[float | None] = mapped_column(Float, default=None)
    # Beslenme (günlük toplam, manuel loglanmışsa)
    nutrition_calories: Mapped[float | None] = mapped_column(Float, default=None)
    nutrition_protein_g: Mapped[float | None] = mapped_column(Float, default=None)
    nutrition_fat_g: Mapped[float | None] = mapped_column(Float, default=None)
    nutrition_carbs_g: Mapped[float | None] = mapped_column(Float, default=None)
    # Diğer sağlık ölçümleri
    blood_pressure_systolic: Mapped[float | None] = mapped_column(Float, default=None)
    blood_pressure_diastolic: Mapped[float | None] = mapped_column(Float, default=None)
    blood_glucose_mmol: Mapped[float | None] = mapped_column(Float, default=None)
    oxygen_saturation_percent: Mapped[float | None] = mapped_column(Float, default=None)
    hydration_liters: Mapped[float | None] = mapped_column(Float, default=None)
    # Health Connect köprüsüyle gelen ek metrikler (2026-07-19)
    resting_heart_rate: Mapped[float | None] = mapped_column(Float, default=None)
    hrv_rmssd_ms: Mapped[float | None] = mapped_column(Float, default=None)
    respiratory_rate: Mapped[float | None] = mapped_column(Float, default=None)
    vo2_max: Mapped[float | None] = mapped_column(Float, default=None)
    floors_climbed: Mapped[int | None] = mapped_column(Integer, default=None)
    body_temperature_celsius: Mapped[float | None] = mapped_column(Float, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class HeartRate(Base):
    """Raw heart rate data points from Google Fit or Health Connect."""
    __tablename__ = "heart_rates"

    id: Mapped[int] = mapped_column(primary_key=True)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    bpm: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class SleepSession(Base):
    """Sleep segment data (evre bazlı — awake/light/deep/rem)."""
    __tablename__ = "sleep_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration_minutes: Mapped[int] = mapped_column(Integer)
    stage: Mapped[str | None] = mapped_column(String(50), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Workout(Base):
    """Exercise/activity sessions from Google Fit (sleep hariç — session activityType != 72)."""
    __tablename__ = "workouts"

    id: Mapped[int] = mapped_column(primary_key=True)
    google_session_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    activity_type: Mapped[str] = mapped_column(String(50))
    name: Mapped[str | None] = mapped_column(String(255), default=None)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration_minutes: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class HealthRecord(Base):
    """Health Connect'in desteklediği tüm kayıt türleri için kayıpsız ham veri deposu.

    Sık kullanılan metrikler ``HealthDay`` üzerinde sorgulanabilir sütunlarda tutulur.
    Bu tablo ise yeni Health Connect kayıt türleri çıktığında şema değişikliği
    gerektirmeden tüm alanları ve kaynak bilgisini saklar.
    """

    __tablename__ = "health_records"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_health_record_source_external"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(50), default="health_connect", index=True)
    external_id: Mapped[str] = mapped_column(String(255))
    record_type: Mapped[str] = mapped_column(String(100), index=True)
    category: Mapped[str] = mapped_column(String(50), index=True)
    title: Mapped[str | None] = mapped_column(String(255), default=None)
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    value: Mapped[float | None] = mapped_column(Float, default=None)
    unit: Mapped[str | None] = mapped_column(String(50), default=None)
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
