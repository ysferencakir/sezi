import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from core.base_module import BaseModule, Schedule

scheduler = AsyncIOScheduler()


def _make_job(module: BaseModule, schedule: Schedule):
    async def job():
        handler = getattr(module, schedule.handler, None)
        if handler is None:
            logger.error(f"[{module.name}] handler '{schedule.handler}' not found")
            return
        try:
            await handler()
        except Exception as exc:
            logger.exception(f"[{module.name}] job '{schedule.job_id}' failed: {exc}")

    return job


def register_module(module: BaseModule) -> None:
    for schedule in module.schedules():
        trigger = CronTrigger.from_crontab(schedule.cron)
        job_fn = _make_job(module, schedule)
        scheduler.add_job(
            job_fn,
            trigger=trigger,
            id=f"{module.name}.{schedule.job_id}",
            name=schedule.description or schedule.job_id,
            replace_existing=True,
        )
        logger.info(f"Scheduled [{module.name}] '{schedule.job_id}' @ {schedule.cron}")


def start() -> None:
    scheduler.start()
    logger.info("Scheduler started")


def stop() -> None:
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")
