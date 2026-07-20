from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from loguru import logger
from pydantic import BaseModel

from api.routers import auth, barcode, context, dashboard, ingest
from core import module_loader, scheduler, telegram_bot
from core.database import create_tables
from core.security import require_admin_token


@asynccontextmanager
async def lifespan(app: FastAPI):
    # load_all() her modülün models.py'sini import ederek Base.metadata'ya kaydeder —
    # create_tables() bundan önce çalışırsa yalnızca dashboard.py'nin doğrudan
    # import ettiği modellerin tabloları oluşur, dashboard'a henüz bağlanmamış
    # yeni modüllerin tabloları sessizce atlanır.
    module_loader.load_all()
    await create_tables()
    scheduler.start()
    await telegram_bot.start()
    yield
    await telegram_bot.stop()
    scheduler.stop()


app = FastAPI(title="Sezi", version="0.1.0", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(barcode.router)
app.include_router(context.router)
app.include_router(dashboard.router)
app.include_router(ingest.router)


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


@app.post("/modules/{name}/run", dependencies=[Depends(require_admin_token)])
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


@app.post("/modules/{name}/trigger/{job_id}", dependencies=[Depends(require_admin_token)])
async def trigger_module_job(name: str, job_id: str):
    """Zamanlanmış bir job'ı (ör. digest.morning_digest) manuel tetikler —
    aynı handler çağrıldığı için sonuç, mevcut veriyle her seferinde tutarlıdır."""
    module = module_loader.get(name)
    if module is None:
        raise HTTPException(status_code=404, detail=f"Module '{name}' not found")

    schedule = next((s for s in module.schedules() if s.job_id == job_id), None)
    if schedule is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found on module '{name}'")

    handler = getattr(module, schedule.handler, None)
    if handler is None:
        raise HTTPException(status_code=500, detail=f"Handler '{schedule.handler}' missing")

    try:
        result = await handler()
        return {"status": "ok", "module": name, "job": job_id, "result": str(result)}
    except Exception as exc:
        logger.exception(f"Manual trigger failed for {name}.{job_id}")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/health")
async def health():
    return {"status": "ok"}


app.mount("/", StaticFiles(directory="static", html=True), name="static")
