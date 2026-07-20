import re
from datetime import date, datetime
from typing import Any

import httpx

# TEFAS'ın resmi public API'si yok — bu, tefas.gov.tr'nin kendi fon fiyat sayfasının
# kullandığı undocumented backend endpoint'i (tefas-crawler ile aynı). Redistribution
# (veriyi ham/toplu şekilde üçüncü taraflara dağıtma) TEFAS tarafından yasak; burada
# sadece kişisel dashboard görüntüleme amacıyla, fon başına günde bir istekle
# (schedule bkz. module.py) kullanılıyor — agresif/toplu scraping yapılmıyor.
_URL = "https://www.tefas.gov.tr/api/funds/fonFiyatBilgiGetir"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.tefas.gov.tr/TarihselVeriler.aspx",
}
# Backend sadece bu sabit ay değerlerini kabul ediyor — en küçüğü (1) günlük
# senkronizasyon için yeterli ve istek boyutunu minimumda tutuyor.
_PERIOD_MONTHS = 1

_DOTNET_DATE_RE = re.compile(r"/Date\((\d+)\)/")


def _parse_tarih(raw: str) -> date:
    match = _DOTNET_DATE_RE.match(raw or "")
    if match:
        return datetime.fromtimestamp(int(match.group(1)) / 1000).date()
    return datetime.fromisoformat(raw).date()


async def fetch_fund_history(fund_code: str) -> list[dict[str, Any]]:
    """Belirtilen fon kodu için son ~1 aylık günlük fiyat geçmişini döner."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            _URL,
            json={"fonKodu": fund_code, "dil": "TR", "periyod": _PERIOD_MONTHS},
            headers=_HEADERS,
            timeout=15.0,
        )
        resp.raise_for_status()
        rows = resp.json().get("resultList", [])

    return [
        {
            "fund_code": row.get("fonKodu", fund_code),
            "title": row.get("fonUnvan"),
            "day": _parse_tarih(row.get("tarih", "")),
            "price": row.get("fiyat"),
        }
        for row in rows
        if row.get("tarih") is not None
    ]
