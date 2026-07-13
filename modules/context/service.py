from datetime import date

from sqlalchemy.dialects.postgresql import insert

from core.database import AsyncSessionFactory
from modules.context.models import WeeklyContext


async def submit_context(
    week_start: date,
    notes: str,
    special_events: str | None = None,
    general_feeling: int | None = None,
) -> None:
    """Insert or update a weekly context entry."""
    values = {
        "week_start": week_start,
        "notes": notes,
        "special_events": special_events,
        "general_feeling": general_feeling,
    }
    stmt = insert(WeeklyContext).values(**values).on_conflict_do_update(
        index_elements=["week_start"], set_=values
    )
    async with AsyncSessionFactory() as session:
        await session.execute(stmt)
        await session.commit()
