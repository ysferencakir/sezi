from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from core.database import AsyncSessionFactory
from modules.weather.models import UserLocation

# Tek satırlık "en son bilinen konum" — id sabit 1
_LOCATION_ID = 1


async def update_location(latitude: float, longitude: float) -> None:
    stmt = insert(UserLocation).values(
        id=_LOCATION_ID, latitude=latitude, longitude=longitude
    ).on_conflict_do_update(
        index_elements=["id"], set_={"latitude": latitude, "longitude": longitude}
    )
    async with AsyncSessionFactory() as session:
        await session.execute(stmt)
        await session.commit()


async def get_location() -> UserLocation | None:
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(UserLocation).where(UserLocation.id == _LOCATION_ID))
        return result.scalar_one_or_none()
