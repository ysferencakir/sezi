import asyncio
import html
import re
from typing import Any

import httpx
from loguru import logger

from core.config import settings

_URL = "https://www.eshot.gov.tr/tr/OtobusumNerede/290"
_MAX_RETRIES = 3
_RETRY_BACKOFF_SECONDS = 2.0

# eshot.gov.tr Render'ın (ve muhtemelen diğer bulut sağlayıcıların) datacenter
# IP aralıklarını engelliyor — ScraperAPI'nin Türkiye IP'li proxy'si üzerinden
# geçerek gerçek bir Türkiye kullanıcısı gibi görünüyoruz. Key boşsa direkt bağlanır
# (local geliştirmede genelde gerekmez, çünkü ev/ofis IP'leri engellenmiyor).
_SCRAPERAPI_PROXY_HOST = "proxy-server.scraperapi.com:8001"


def _client_kwargs() -> dict[str, Any]:
    if not settings.scraperapi_key:
        return {"timeout": 15.0}
    # eshot.gov.tr "korumalı domain" sayıldığı için premium=true şart — düz proxy
    # modu 500 döndürüyor. Premium proxy istekleri daha yavaş olabiliyor (ScraperAPI
    # dokümantasyonu 60-70sn öneriyor), bu yüzden timeout yüksek tutuluyor.
    proxy_url = (
        f"http://scraperapi.country_code=tr.premium=true:"
        f"{settings.scraperapi_key}@{_SCRAPERAPI_PROXY_HOST}"
    )
    # ScraperAPI proxy modu HTTPS trafiğini kendi sertifikasıyla MITM ediyor —
    # bu yüzden sertifika doğrulaması kapatılmalı (ScraperAPI'nin kendi dokümantasyonu).
    return {"timeout": 70.0, "proxy": proxy_url, "verify": False}

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
            async with httpx.AsyncClient(**_client_kwargs()) as client:
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
