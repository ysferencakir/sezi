from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import select

from core.base_module import BaseModule, Schedule
from core.database import AsyncSessionFactory
from core.notifier import notifier
from modules.calendar.models import CalendarDay
from modules.currency.models import CurrencyDay
from modules.health.models import HealthDay, SleepSession, Workout
from modules.smoking.models import SmokingDay
from modules.spotify.models import PlayedTrack
from modules.weather.models import WeatherDay


class DigestModule(BaseModule):
    """Diğer modüllerin verilerini okuyup sabah/akşam için tek bir birleşik
    özet bildirimi kurar — kendi verisi yok, sadece rapor katmanı.
    """

    name = "digest"
    description = "Sabah ve akşam için birleşik Telegram özeti"

    def schedules(self) -> list[Schedule]:
        return [
            Schedule("morning_digest", "40 8 * * *", "morning_digest", "Sabah özeti (hava, takvim, uyku, döviz)"),
            Schedule("evening_digest", "45 22 * * *", "evening_digest", "Akşam özeti (adım, sigara, context hatırlatma)"),
        ]

    async def fetch(self) -> Any:
        return None

    async def process(self, data: Any) -> Any:
        return None

    # --- Sabah ---

    async def morning_digest(self) -> str:
        async with AsyncSessionFactory() as session:
            weather = (
                await session.execute(select(WeatherDay).order_by(WeatherDay.day.desc()).limit(1))
            ).scalar_one_or_none()
            calendar = (
                await session.execute(select(CalendarDay).order_by(CalendarDay.day.desc()).limit(1))
            ).scalar_one_or_none()
            sleep = (
                await session.execute(select(SleepSession).order_by(SleepSession.start_time.desc()).limit(1))
            ).scalar_one_or_none()
            currency = (
                await session.execute(select(CurrencyDay).order_by(CurrencyDay.day.desc()).limit(1))
            ).scalar_one_or_none()

        lines = ["<b>🌅 Günaydın</b>"]

        if weather:
            wind = f", rüzgar {weather.wind_speed_max:.0f} km/s" if weather.wind_speed_max is not None else ""
            pollen_bits = [
                f"{name} {val:.1f}"
                for name, val in (
                    ("huş", weather.birch_pollen), ("çim", weather.grass_pollen), ("ambrosia", weather.ragweed_pollen),
                )
                if val
            ]
            pollen = f", polen: {', '.join(pollen_bits)}" if pollen_bits else ""
            lines.append(
                f"☁️ Hava ({weather.day}): {weather.temp_min:.0f}-{weather.temp_max:.0f}°C, "
                f"{weather.condition or '-'}, AQI {weather.european_aqi if weather.european_aqi is not None else '-'}"
                f"{wind}{pollen}"
            )
        else:
            lines.append("☁️ Hava: henüz veri yok")

        if calendar:
            holiday = f" 🎌 {calendar.holiday_name}" if calendar.is_holiday else ""
            lines.append(
                f"📅 Takvim ({calendar.day}){holiday}: {calendar.meeting_count} toplantı, "
                f"{calendar.meeting_minutes} dk, en yoğun saat {calendar.busiest_hour if calendar.busiest_hour is not None else '-'}, "
                f"en uzun boş blok {calendar.free_consecutive_hours or 0:.1f} saat"
            )
        else:
            lines.append("📅 Takvim: henüz veri yok")

        if sleep:
            stage = f" ({sleep.stage})" if sleep.stage else ""
            lines.append(f"😴 Uyku ({sleep.start_time.date()}): {sleep.duration_minutes} dk{stage}")
        else:
            lines.append("😴 Uyku: henüz veri yok")

        if currency:
            lines.append(
                f"💱 USD/TRY {currency.usd_try:.2f} · EUR/TRY {currency.eur_try:.2f}"
                + (f" · GBP/TRY {currency.gbp_try:.2f}" if currency.gbp_try else "")
            )
        else:
            lines.append("💱 Döviz: henüz veri yok")

        msg = "\n".join(lines)
        await notifier.send(msg, title="Sabah Özeti")
        return msg

    # --- Akşam ---

    async def evening_digest(self) -> str:
        today = date.today()

        async with AsyncSessionFactory() as session:
            health = (
                await session.execute(select(HealthDay).order_by(HealthDay.day.desc()).limit(1))
            ).scalar_one_or_none()
            smoking = (
                await session.execute(select(SmokingDay).where(SmokingDay.day == today))
            ).scalar_one_or_none()
            workouts = (
                await session.execute(
                    select(Workout).order_by(Workout.start_time.desc()).limit(3)
                )
            ).scalars().all()
            today_start = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)
            tracks = (
                await session.execute(
                    select(PlayedTrack)
                    .where(PlayedTrack.played_at >= today_start)
                    .order_by(PlayedTrack.played_at.desc())
                )
            ).scalars().all()

        lines = ["<b>🌙 Günün Özeti</b>"]

        if health:
            weight = f" · ⚖️ {health.weight_kg:.1f} kg" if health.weight_kg else ""
            lines.append(f"👟 Adım ({health.day}): {health.steps:,}{weight}")
        else:
            lines.append("👟 Adım: henüz veri yok")

        if workouts:
            latest = workouts[0]
            lines.append(f"🏋️ Son antrenman: {latest.activity_type} ({latest.duration_minutes} dk, {latest.start_time.date()})")

        lines.append(f"🚬 Sigara (bugün): {smoking.count if smoking else 0}")

        if tracks:
            top_artists = []
            seen = set()
            for t in tracks:
                if t.artist_name not in seen:
                    seen.add(t.artist_name)
                    top_artists.append(t.artist_name)
            lines.append(f"🎵 Bugün {len(tracks)} parça — {', '.join(top_artists[:3])}")

        lines.append("📝 Bota /context yazarak haftanı değerlendir")

        msg = "\n".join(lines)
        await notifier.send(msg, title="Akşam Özeti")
        return msg
