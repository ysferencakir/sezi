from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Schedule:
    """Defines when a module job should run."""
    job_id: str
    cron: str          # e.g. "0 8 * * *" = every day at 08:00
    handler: str       # method name on the module to call
    description: str = ""


class BaseModule(ABC):
    """
    All modules must inherit this class and implement fetch() and process().
    Optionally override schedules() to register recurring jobs.
    """

    name: str = ""
    description: str = ""

    @abstractmethod
    async def fetch(self) -> Any:
        """Pull raw data from the external source."""
        ...

    @abstractmethod
    async def process(self, data: Any) -> Any:
        """Transform/store the fetched data."""
        ...

    def schedules(self) -> list[Schedule]:
        """Return scheduled jobs for this module. Override to add jobs."""
        return []

    async def run(self) -> Any:
        """Convenience: fetch + process in one call."""
        data = await self.fetch()
        return await self.process(data)

    def __repr__(self) -> str:
        return f"<Module: {self.name}>"
