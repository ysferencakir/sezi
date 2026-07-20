from fastapi import Header, HTTPException

from core.config import settings


def require_admin_token(x_admin_token: str | None = Header(default=None)) -> None:
    """Modül tetikleme ve yazma uçları için paylaşımlı sır kontrolü.

    HEALTH_INGEST_TOKEN'daki desenle aynı: ADMIN_TOKEN boşsa uç kapalıdır (503),
    yanlış/eksik token'da 401 döner.
    """
    if not settings.admin_token:
        raise HTTPException(status_code=503, detail="Admin endpoints disabled: ADMIN_TOKEN not configured")
    if x_admin_token != settings.admin_token:
        raise HTTPException(status_code=401, detail="Invalid admin token")
