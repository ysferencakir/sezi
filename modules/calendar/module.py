from datetime import datetime, timedelta, timezone
from typing import Any

from loguru import logger
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from core.base_module import BaseModule, Schedule
from core.database import AsyncSessionFactory
from core.notifier import notifier
from modules.calendar import google_calendar, holidays
from modules.calendar.categories import categorize
from modules.calendar.models import CalendarDay, CalendarEvent
from modules.health import google_fit
from modules.health.models import OAuthToken

# Meşgul aralık dışındaki en uzun boşluğu hesaplarken kullanılan çalışma saatleri
# (etkinliğin kendi saat dilimine göre — bkz. _longest_free_gap)
_WORK_START_HOUR = 8
_WORK_END_HOUR = 22


class CalendarModule(BaseModule):
    name = "calendar"
    description = "Google Calendar üzerinden günlük toplantı özeti"

    def schedules(self) -> list[Schedule]:
        return [
            Schedule("daily_sync", "15 7 * * *", "run", "Dün'ün takvim verisini çek"),
            Schedule("morning_report", "35 8 * * *", "morning_report", "Sabah takvim özeti bildirimi"),
        ]

    # --- Token yönetimi (health modülüyle aynı "google" token'ı paylaşır) ---

    async def _get_token(self) -> OAuthToken | None:
        async with AsyncSessionFactory() as session:
            result = await session.execute(
                select(OAuthToken).where(OAuthToken.provider == "google")
            )
            return result.scalar_one_or_none()

    async def _fresh_access_token(self) -> str | None:
        token = await self._get_token()
        if token is None:
            logger.warning("[calendar] Google OAuth token bulunamadı — önce /auth/google ile yetkilendir")
            return None

        if token.expires_at > datetime.now(timezone.utc) + timedelta(minutes=5):
            return token.access_token

        data = await google_fit.refresh_access_token(token.refresh_token)
        async with AsyncSessionFactory() as session:
            token.access_token = data["access_token"]
            token.expires_at = datetime.now(timezone.utc) + timedelta(seconds=data["expires_in"])
            session.add(token)
            await session.commit()

        return data["access_token"]

    # --- BaseModule ---

    async def fetch(self) -> dict[str, Any]:
        access_token = await self._fresh_access_token()
        if not access_token:
            return {}

        yesterday = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        today = yesterday + timedelta(days=1)

        events = await google_calendar.fetch_events(access_token, yesterday, today)
        return {"date": yesterday.date(), "events": events}

    async def process(self, data: dict[str, Any]) -> dict[str, Any]:
        if not data:
            return {}

        day = data["date"]
        summary = self._summarize(data["events"], day)
        summary["is_holiday"] = await holidays.is_public_holiday(day)
        event_rows = self._extract_events(data["events"], day)

        async with AsyncSessionFactory() as session:
            stmt = insert(CalendarDay).values(**summary).on_conflict_do_update(
                index_elements=["day"], set_=summary
            )
            await session.execute(stmt)

            for row in event_rows:
                event_stmt = insert(CalendarEvent).values(**row).on_conflict_do_update(
                    index_elements=["google_event_id"], set_=row
                )
                await session.execute(event_stmt)

            await session.commit()

        logger.info(f"[calendar] {day} kaydedildi — {summary['meeting_count']} toplantı, {summary['meeting_minutes']} dk")
        return summary

    # --- Bildirim ---

    async def morning_report(self) -> None:
        async with AsyncSessionFactory() as session:
            result = await session.execute(
                select(CalendarDay).order_by(CalendarDay.day.desc()).limit(1)
            )
            row = result.scalar_one_or_none()

        if row is None:
            return

        msg = (
            f"<b>Sabah Takvim Özeti — {row.day}</b>\n"
            f"{'🎌 Resmi tatil' if row.is_holiday else ''}\n"
            f"📅 Toplantı: {row.meeting_count}\n"
            f"⏱ Toplam süre: {row.meeting_minutes} dk\n"
            f"🕐 En yoğun saat: {row.busiest_hour if row.busiest_hour is not None else '-'}\n"
            f"🌤 En uzun boş blok: {row.free_consecutive_hours or 0:.1f} saat"
        )
        await notifier.send(msg, title="Takvim Özeti")

    # --- Yardımcı ---

    def _summarize(self, events: list[dict], day) -> dict:
        meeting_count = 0
        meeting_minutes = 0
        hour_counts: dict[int, int] = {}
        intervals: list[tuple[datetime, datetime]] = []

        for event in events:
            start_raw = event.get("start", {}).get("dateTime")
            end_raw = event.get("end", {}).get("dateTime")
            if not start_raw or not end_raw:
                continue  # tüm gün süren etkinlikleri (sadece "date" alanı olanları) atla

            start = datetime.fromisoformat(start_raw)
            end = datetime.fromisoformat(end_raw)
            meeting_count += 1
            meeting_minutes += int((end - start).total_seconds() / 60)
            hour_counts[start.hour] = hour_counts.get(start.hour, 0) + 1
            intervals.append((start, end))

        busiest_hour = max(hour_counts, key=hour_counts.get) if hour_counts else None
        free_hours = self._longest_free_gap(intervals, day)

        return {
            "day": day,
            "meeting_count": meeting_count,
            "meeting_minutes": meeting_minutes,
            "busiest_hour": busiest_hour,
            "free_consecutive_hours": free_hours,
        }

    def _extract_events(self, events: list[dict], day) -> list[dict]:
        rows = []
        for event in events:
            start_raw = event.get("start", {}).get("dateTime")
            end_raw = event.get("end", {}).get("dateTime")
            event_id = event.get("id")
            if not start_raw or not end_raw or not event_id:
                continue

            start = datetime.fromisoformat(start_raw)
            end = datetime.fromisoformat(end_raw)
            title = event.get("summary", "")

            rows.append({
                "google_event_id": event_id,
                "day": day,
                "title": title,
                "category": categorize(title),
                "start_time": start,
                "end_time": end,
                "duration_minutes": int((end - start).total_seconds() / 60),
            })
        return rows

    def _longest_free_gap(self, intervals: list[tuple[datetime, datetime]], day) -> float:
        """08:00-22:00 çalışma penceresi içindeki en uzun kesintisiz boş bloğu (saat) döndürür."""
        tz = intervals[0][0].tzinfo if intervals else timezone.utc
        window_start = datetime.combine(day, datetime.min.time(), tzinfo=tz).replace(hour=_WORK_START_HOUR)
        window_end = datetime.combine(day, datetime.min.time(), tzinfo=tz).replace(hour=_WORK_END_HOUR)

        busy = sorted(
            (max(s, window_start), min(e, window_end))
            for s, e in intervals
            if e > window_start and s < window_end
        )

        longest = timedelta(0)
        cursor = window_start
        for start, end in busy:
            if start > cursor:
                longest = max(longest, start - cursor)
            cursor = max(cursor, end)
        longest = max(longest, window_end - cursor)

        return round(longest.total_seconds() / 3600, 1)
