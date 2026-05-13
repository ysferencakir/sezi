from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from loguru import logger
from pydantic import BaseModel

from core import module_loader, scheduler
from core.database import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    module_loader.load_all()
    scheduler.start()
    yield
    scheduler.stop()


app = FastAPI(title="Sezi", version="0.1.0", lifespan=lifespan)


class ModuleInfo(BaseModel):
    name: str
    description: str
    schedule_count: int


@app.get("/modules", response_model=list[ModuleInfo])
async def list_modules():
    return [
        ModuleInfo(
            name=m.name,
            description=m.description,
            schedule_count=len(m.schedules()),
        )
        for m in module_loader.all_modules()
    ]


@app.post("/modules/{name}/run")
async def run_module(name: str):
    module = module_loader.get(name)
    if module is None:
        raise HTTPException(status_code=404, detail=f"Module '{name}' not found")
    try:
        result = await module.run()
        return {"status": "ok", "module": name, "result": str(result)}
    except Exception as exc:
        logger.exception(f"Manual run failed for module '{name}'")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/health")
async def health():
    return {"status": "ok"}
