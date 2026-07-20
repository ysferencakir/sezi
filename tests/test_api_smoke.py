import httpx

from api.main import app
from core import module_loader
from core.config import settings


async def _client():
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://test")


async def test_health_endpoint():
    async with await _client() as client:
        r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


async def test_modules_list_includes_new_modules():
    module_loader.load_all()
    async with await _client() as client:
        r = await client.get("/modules")
    assert r.status_code == 200
    names = {m["name"] for m in r.json()}
    assert {"gold", "stocks", "tefas", "evds", "events", "strava", "bank", "energy"} <= names


async def test_run_module_blocked_without_admin_token(monkeypatch):
    monkeypatch.setattr(settings, "admin_token", "")
    async with await _client() as client:
        r = await client.post("/modules/currency/run")
    assert r.status_code == 503


async def test_run_module_rejects_wrong_admin_token(monkeypatch):
    monkeypatch.setattr(settings, "admin_token", "correct-token")
    async with await _client() as client:
        r = await client.post("/modules/currency/run", headers={"X-Admin-Token": "wrong"})
    assert r.status_code == 401


async def test_run_module_404_for_unknown_module(monkeypatch):
    monkeypatch.setattr(settings, "admin_token", "correct-token")
    async with await _client() as client:
        r = await client.post("/modules/does-not-exist/run", headers={"X-Admin-Token": "correct-token"})
    assert r.status_code == 404
