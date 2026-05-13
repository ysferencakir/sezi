from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from core.database import AsyncSessionFactory
from modules.health import google_fit
from modules.health.models import OAuthToken

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/google")
async def google_login():
    """Tarayıcıda aç → Google yetkilendirme sayfasına yönlendirir."""
    url = google_fit.build_auth_url()
    return RedirectResponse(url)


@router.get("/google/callback")
async def google_callback(code: str, state: str = "", error: str = ""):
    if error:
        raise HTTPException(status_code=400, detail=f"Google OAuth hatası: {error}")

    data = await google_fit.exchange_code(code)

    async with AsyncSessionFactory() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(OAuthToken).where(OAuthToken.provider == "google")
        )
        token = result.scalar_one_or_none()

        expires_at = datetime.now(timezone.utc) + timedelta(seconds=data.get("expires_in", 3600))

        if token:
            token.access_token = data["access_token"]
            token.expires_at = expires_at
            if "refresh_token" in data:
                token.refresh_token = data["refresh_token"]
        else:
            token = OAuthToken(
                provider="google",
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token", ""),
                expires_at=expires_at,
            )
            session.add(token)

        await session.commit()

    return {"status": "ok", "message": "Google Fit yetkilendirmesi başarılı"}
