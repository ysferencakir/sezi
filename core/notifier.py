import asyncio
from loguru import logger

from core.config import settings


class Notifier:
    """Send notifications via ntfy.sh and/or Telegram."""

    async def send(self, message: str, title: str = "Sezi") -> None:
        """Send notification to every configured channel."""
        await self._send_ntfy(message, title)
        await self._send_telegram(message, title)

    async def _send_ntfy(self, message: str, title: str) -> None:
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
            logger.info(f"ntfy notification sent: [{title}] {message}")
        except Exception as e:
            logger.error(f"Failed to send ntfy notification: {e}")

    async def _send_telegram(self, message: str, title: str) -> None:
        if not settings.telegram_bot_token or not settings.telegram_chat_id:
            logger.info(f"[{title}] {message} (Telegram disabled)")
            return

        try:
            import httpx

            url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
            payload = {
                "chat_id": settings.telegram_chat_id,
                "text": f"<b>{title}</b>\n{message}",
                "parse_mode": "HTML",
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=5.0)
                response.raise_for_status()
            logger.info(f"Telegram notification sent: [{title}] {message}")
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")


notifier = Notifier()
