from typing import Any

import httpx

from core.config import settings

# camgoz.net "Türkiye Market Ürünleri Barkod API" — bireysel kullanım için ücretsiz.
# Gerçek endpoint şeması https://camgoz.net/v3/api-docs (Spring/springdoc OpenAPI) 'tan
# doğrulandı: GET /api/external/search?query=<barkod veya anahtar kelime>.
#
# ÖNEMLİ: camgoz.net'e doğrudan istek atmak 400 ile reddediliyor —
# {"error":"Access to this API is restricted to the JOJ API platform only.
# You can reach it here: https://jojapi.com/api/product-barcode-api"}.
# Yani tüm istekler JoJ API Marketplace gateway'i üzerinden geçmeli; gateway'in
# gerçek base URL'i ve auth header adı ancak jojapi.com'da key alındıktan sonra
# dashboard'da görünüyor (otomatik keşfedilemedi). Key alınınca CAMGOZ_API_BASE'i
# gateway adresiyle güncelle — endpoint path'i (/api/external/search) değişmemeli.
_SEARCH_PATH = "/api/external/search"


async def lookup(barcode: str) -> dict[str, Any] | None:
    """Barkod numarasına göre ürün adı/fiyat/market bilgisini döner."""
    headers = {"X-API-Key": settings.camgoz_api_key} if settings.camgoz_api_key else {}
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.camgoz_api_base}{_SEARCH_PATH}",
            params={"query": barcode, "marketPrices": "true"},
            headers=headers,
            timeout=15.0,
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
