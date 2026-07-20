from typing import Any
from xml.etree import ElementTree

import httpx

_RSS_URL = "https://etkinlik.io/rss/sorgu"
# Etkinlik.io tam API'si (X-Etkinlik-Token) başvuru/onay gerektiriyor; auth gerektirmeyen
# genel RSS akışı üzerinden çekiliyor. Şehir/kategori filtresi resmi olarak dokümante
# değil — bu yüzden akışın tamamı çekilip modül tarafında başlıkta/açıklamada
# anahtar kelime araması yapılarak filtreleniyor (bkz. module.py).


async def fetch_feed() -> list[dict[str, Any]]:
    """Etkinlik.io genel RSS akışındaki tüm etkinlikleri döner."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(_RSS_URL, timeout=15.0)
        resp.raise_for_status()
        root = ElementTree.fromstring(resp.text)

    items = []
    for item in root.findall(".//item"):
        title = item.findtext("title") or ""
        link = item.findtext("link") or ""
        if not link:
            continue
        items.append({
            "title": title,
            "link": link,
            "description": item.findtext("description") or "",
            "pub_date": item.findtext("pubDate") or "",
            "category": item.findtext("category") or "",
        })
    return items
