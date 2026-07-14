from datetime import datetime, timedelta, timezone
from typing import Any

from loguru import logger
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from core.base_module import BaseModule, Schedule
from core.database import AsyncSessionFactory
from modules.health.models import OAuthToken
from modules.spotify import spotify_client
from modules.spotify.models import PlayedTrack


class SpotifyModule(BaseModule):
    name = "spotify"
    description = "Spotify dinleme geçmişi"

    def schedules(self) -> list[Schedule]:
        return [
            Schedule("daily_sync", "5 7 * * *", "run", "Son 24 saatte çalınan parçaları çek"),
        ]

    # --- Token yönetimi (ayrı provider="spotify" — Google'dan bağımsız) ---

    async def _get_token(self) -> OAuthToken | None:
        async with AsyncSessionFactory() as session:
            result = await session.execute(
                select(OAuthToken).where(OAuthToken.provider == "spotify")
            )
            return result.scalar_one_or_none()

    async def _fresh_access_token(self) -> str | None:
        token = await self._get_token()
        if token is None:
            logger.warning("[spotify] OAuth token bulunamadı — önce /auth/spotify/authorize ile yetkilendir")
            return None

        if token.expires_at > datetime.now(timezone.utc) + timedelta(minutes=5):
            return token.access_token

        data = await spotify_client.refresh_access_token(token.refresh_token)
        async with AsyncSessionFactory() as session:
            token.access_token = data["access_token"]
            token.expires_at = datetime.now(timezone.utc) + timedelta(seconds=data["expires_in"])
            # Spotify refresh isteğinde yeni refresh_token dönmeyebilir — dönerse güncelle.
            if data.get("refresh_token"):
                token.refresh_token = data["refresh_token"]
            session.add(token)
            await session.commit()

        return data["access_token"]

    # --- BaseModule ---

    async def _last_played_at(self) -> datetime | None:
        async with AsyncSessionFactory() as session:
            result = await session.execute(
                select(PlayedTrack).order_by(PlayedTrack.played_at.desc()).limit(1)
            )
            row = result.scalar_one_or_none()
            return row.played_at if row else None

    async def fetch(self) -> dict[str, Any]:
        access_token = await self._fresh_access_token()
        if not access_token:
            return {}

        last_played = await self._last_played_at()
        after = last_played or (datetime.now(timezone.utc) - timedelta(days=1))
        after_ms = int(after.timestamp() * 1000)

        items = await spotify_client.fetch_recently_played(access_token, after_ms)
        return {"items": items}

    async def process(self, data: dict[str, Any]) -> dict[str, Any]:
        if not data:
            return {}

        rows = self._parse_items(data["items"])
        if not rows:
            return {"new_tracks": 0}

        async with AsyncSessionFactory() as session:
            for row in rows:
                stmt = insert(PlayedTrack).values(**row).on_conflict_do_nothing(
                    index_elements=["played_at"]
                )
                await session.execute(stmt)
            await session.commit()

        logger.info(f"[spotify] {len(rows)} yeni parça kaydedildi")
        return {"new_tracks": len(rows)}

    def _parse_items(self, items: list[dict]) -> list[dict]:
        rows = []
        for item in items:
            track = item.get("track", {})
            played_at_raw = item.get("played_at")
            if not track.get("id") or not played_at_raw:
                continue
            rows.append({
                "spotify_track_id": track["id"],
                "played_at": datetime.fromisoformat(played_at_raw.replace("Z", "+00:00")),
                "track_name": track.get("name", ""),
                "artist_name": ", ".join(a.get("name", "") for a in track.get("artists", [])),
                "album_name": track.get("album", {}).get("name"),
                "duration_ms": track.get("duration_ms"),
            })
        return rows
