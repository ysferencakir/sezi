import asyncio
import html
import re
from typing import Any

import httpx
from loguru import logger

_URL = "https://www.eshot.gov.tr/tr/OtobusumNerede/290"
_MAX_RETRIES = 3
_RETRY_BACKOFF_SECONDS = 2.0

# Sayfa <td>HAT</td><td>HAT ADI</td><td>MESAFE</td><td>KALAN SÜRE</td> satırları döndürüyor.
_TD_RE = re.compile(r"<td[^>]*>\s*([^<]*?)\s*</td>", re.IGNORECASE)
_TABLE_RE = re.compile(
    r'<table class="table table-bordered table-striped table-hover">.*?</table>',
    re.IGNORECASE | re.DOTALL,
)


async def _post_with_retry(hat_id: str, durak_id: str, yon: int) -> str:
    """Ağ hatalarında (timeout/bağlantı kopması) artan bekleme ile yeniden dener.
    Render gibi bazı barındırma sağlayıcılarından siteye ilk bağlantı zaman aşımına
    uğrayabiliyor — bu genelde kalıcı bir IP engeli değil, geçici bir ağ sorunu."""
    last_exc: Exception | None = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    _URL,
                    data={"hatId": hat_id, "durakId": durak_id, "hatYon": str(yon)},
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
                        ),
                    },
                )
                resp.raise_for_status()
                return resp.text
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            last_exc = exc
            if attempt < _MAX_RETRIES:
                wait = _RETRY_BACKOFF_SECONDS * attempt
                logger.warning(
                    f"[eshot_scraper] deneme {attempt}/{_MAX_RETRIES} başarısız "
                    f"({type(exc).__name__}) — {wait:.0f}sn sonra tekrar denenecek"
                )
                await asyncio.sleep(wait)

    raise last_exc


async def fetch_arrivals(durak_id: str, hat_id: str, yon: int) -> list[dict[str, Any]]:
    """ESHOT'un resmi 'Otobüsüm Nerede' sayfasını (form POST ile) sorgulayıp
    gerçek mesafe/süre bilgisiyle yaklaşan otobüsleri döner.

    Not: Bu bir public API değil, ESHOT'un kendi web sayfasının HTML çıktısını
    parse ediyoruz (sayfa yapısı değişirse kırılabilir). `hatId` sadece
    sayfa başlığını belirliyor gibi görünüyor — asıl filtre `durakId` + `hatYon`.
    """
    body = await _post_with_retry(hat_id, durak_id, yon)

    table_match = _TABLE_RE.search(body)
    if not table_match:
        return []

    cells = [html.unescape(c).strip() for c in _TD_RE.findall(table_match.group(0))]
    # İlk 4 hücre başlık (HAT, HAT ADI, DURAĞA MESAFE, KALAN SÜRE) — atla.
    cells = cells[4:]

    rows = []
    for i in range(0, len(cells) - 3, 4):
        hat, hat_adi, mesafe, sure = cells[i:i + 4]
        if not hat:
            continue
        rows.append({
            "hat": hat,
            "hat_adi": hat_adi,
            "mesafe": mesafe,
            "sure": sure,
            "at_stop": mesafe.lower() == "durakta",
        })
    return rows
