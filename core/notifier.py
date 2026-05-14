import asyncio
from loguru import logger

from core.config import settings


class Notifier:
    """Send notifications via ntfy.sh and optional Telegram."""

    async def send(self, message: str, title: str = "Sezi") -> None:
        """Send notification to ntfy.sh topic."""
        if not settings.ntfy_topic:
            logger.info(f"[{title}] {message} (ntfy.sh disabled)")
            return

        try:
            import httpx
            
            headers = {"Title": title}
            if settings.ntfy_token:
                headers["Authorization"] = f"Bearer {settings.ntfy_token}"

            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{settings.ntfy_url}/{settings.ntfy_topic}",
                    content=message,
                    headers=headers,
                    timeout=5.0,
                )
            logger.info(f"Notification sent: [{title}] {message}")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")


notifier = Notifier()
