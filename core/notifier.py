from abc import ABC, abstractmethod

from loguru import logger

from core.config import settings


class NotificationChannel(ABC):
    @abstractmethod
    async def send(self, message: str, title: str = "Sezi") -> None: ...


class NtfyChannel(NotificationChannel):
    """
    ntfy.sh push notifications.
    Daha fazla bilgi: https://ntfy.sh/docs/publish/
    """

    def __init__(self, url: str, topic: str, token: str = "") -> None:
        self._url = url.rstrip("/")
        self._topic = topic
        self._token = token

    async def send(self, message: str, title: str = "Sezi") -> None:
        if not self._topic:
            logger.warning("NTFY_TOPIC ayarlanmamış, bildirim atlandı")
            return

        import httpx

        headers = {"Title": title, "Content-Type": "text/plain; charset=utf-8"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self._url}/{self._topic}",
                content=message.encode("utf-8"),
                headers=headers,
            )
            resp.raise_for_status()


class LogChannel(NotificationChannel):
    """Fallback: bildirimi sadece loglar."""

    async def send(self, message: str, title: str = "Sezi") -> None:
        logger.info(f"[NOTIFY] {title}: {message}")


class Notifier:
    def __init__(self, channels: list[NotificationChannel]) -> None:
        self._channels = channels

    async def send(self, message: str, title: str = "Sezi") -> None:
        for channel in self._channels:
            try:
                await channel.send(message, title)
            except Exception as exc:
                logger.error(f"Bildirim hatası ({channel.__class__.__name__}): {exc}")


def build_notifier() -> Notifier:
    channels: list[NotificationChannel] = [LogChannel()]
    if settings.ntfy_topic:
        channels.append(NtfyChannel(settings.ntfy_url, settings.ntfy_topic, settings.ntfy_token))
    return Notifier(channels)


notifier = build_notifier()
