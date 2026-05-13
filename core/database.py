from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from core.config import settings

# asyncpg sslmode query parametresini desteklemez; URL'den çıkarıp connect_args'a taşıyoruz
_db_url = settings.database_url.replace("?sslmode=require", "").replace("&sslmode=require", "")
_connect_args = {"ssl": "require"} if "neon.tech" in settings.database_url else {}
engine = create_async_engine(_db_url, echo=settings.is_dev, connect_args=_connect_args)
AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class ModuleRecord(Base):
    """Generic log entry written by any module after each run."""
    __tablename__ = "module_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    module_name: Mapped[str] = mapped_column(String(64), index=True)
    event: Mapped[str] = mapped_column(String(64))       # e.g. "fetch", "process", "notify"
    payload: Mapped[str | None] = mapped_column(default=None)  # JSON string
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


async def get_session() -> AsyncSession:
    async with AsyncSessionFactory() as session:
        yield session


async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
