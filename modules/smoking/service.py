from datetime import date

from sqlalchemy.dialects.postgresql import insert

from core.database import AsyncSessionFactory
from modules.smoking.models import SmokingDay


async def submit_count(day: date, count: int) -> None:
    """Insert or update the cigarette count for a given day."""
    values = {"day": day, "count": count}
    stmt = insert(SmokingDay).values(**values).on_conflict_do_update(
        index_elements=["day"], set_=values
    )
    async with AsyncSessionFactory() as session:
        await session.execute(stmt)
        await session.commit()
