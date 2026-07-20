from datetime import date

from core.database import AsyncSessionFactory
from modules.watchlog import tmdb_client
from modules.watchlog.models import WatchLog
from modules.watchlog.parser import parse_watch_text


async def log_watch(raw_text: str, day: date | None = None) -> WatchLog:
    """Serbest metni ayrıştırıp TMDB ile zenginleştirir ve kaydeder."""
    parsed = parse_watch_text(raw_text)
    match = await tmdb_client.search(parsed["title"])

    row = WatchLog(
        day=day or date.today(),
        raw_text=raw_text,
        season=parsed["season"],
        episode=parsed["episode"],
        matched=match is not None,
        tmdb_id=match["tmdb_id"] if match else None,
        media_type=match["media_type"] if match else None,
        title=match["title"] if match else parsed["title"],
        overview=match["overview"] if match else None,
        poster_path=match["poster_path"] if match else None,
        release_date=match["release_date"] if match else None,
    )

    async with AsyncSessionFactory() as session:
        session.add(row)
        await session.commit()
        await session.refresh(row)

    return row
