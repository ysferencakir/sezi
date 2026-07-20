from datetime import datetime, timezone
from typing import Any

import httpx

_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
# Resmi olmayan (public ama undocumented) Yahoo Finance chart endpoint'i.
# BIST hisseleri ".IS" suffix'iyle geliyor (ör. ISCTR.IS, XU100.IS). Auth gerekmiyor
# ama User-Agent'sız istekler bazen 429 dönüyor.
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
}


async def fetch_last_daily_bar(symbol: str) -> dict[str, Any] | None:
    """Son tamamlanmış günlük mum (OHLCV) verisini döner. Veri yoksa None."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            _CHART_URL.format(symbol=symbol),
            params={"interval": "1d", "range": "5d"},
            headers=_HEADERS,
            timeout=15.0,
        )
        resp.raise_for_status()
        body = resp.json()

    result = (body.get("chart", {}).get("result") or [None])[0]
    if not result:
        return None

    timestamps = result.get("timestamp") or []
    quote = (result.get("indicators", {}).get("quote") or [{}])[0]
    if not timestamps or not quote.get("close"):
        return None

    idx = len(timestamps) - 1
    while idx >= 0 and quote["close"][idx] is None:
        idx -= 1
    if idx < 0:
        return None

    return {
        "day": datetime.fromtimestamp(timestamps[idx], tz=timezone.utc).date(),
        "open": quote.get("open", [None] * len(timestamps))[idx],
        "high": quote.get("high", [None] * len(timestamps))[idx],
        "low": quote.get("low", [None] * len(timestamps))[idx],
        "close": quote["close"][idx],
        "volume": quote.get("volume", [None] * len(timestamps))[idx],
    }
