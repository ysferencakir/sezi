from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from core.config import settings
from core.database import AsyncSessionFactory
from modules.calendar import google_calendar
from modules.health import google_fit
from modules.health.models import OAuthToken

router = APIRouter(prefix="/auth", tags=["auth"])

# Tüm Google entegrasyonları (health, calendar, ...) tek token altında toplanır —
# yeni bir modül yeni scope eklediğinde burada birleştirilir ve kullanıcı tekrar yetkilendirir.
_GOOGLE_SCOPES = google_fit.SCOPES + google_calendar.SCOPES


@router.get("/google/authorize")
async def authorize_google():
    """Return Google OAuth authorization URL."""
    auth_url = google_fit.build_auth_url(scopes=_GOOGLE_SCOPES)
    return {"url": auth_url, "message": "Redirect user to this URL to authorize"}


@router.get("/google/callback")
async def callback_google(code: str = Query(...), state: str = Query(None)):
    """Handle Google OAuth callback and store token."""
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    try:
        token_data = await google_fit.exchange_code(code)
    except Exception as e:
        logger.error(f"Failed to exchange code: {e}")
        raise HTTPException(status_code=400, detail="Failed to exchange authorization code")

    # Calculate expiration time
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_data.get("expires_in", 3600))

    # Store token in database
    stmt = insert(OAuthToken).values(
        provider="google",
        access_token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token", ""),
        expires_at=expires_at,
    ).on_conflict_do_update(
        index_elements=["provider"],
        set_=dict(
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token", ""),
            expires_at=expires_at,
            updated_at=datetime.now(timezone.utc),
        ),
    )

    try:
        async with AsyncSessionFactory() as session:
            await session.execute(stmt)
            await session.commit()
        logger.info("Google OAuth token stored successfully")
        return {
            "status": "success",
            "message": "Authorization successful. Token stored.",
            "expires_at": expires_at.isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to store token: {e}")
        raise HTTPException(status_code=500, detail="Failed to store authorization token")
