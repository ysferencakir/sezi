import httpx
import respx

from modules.events import etkinlik_client

SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
<item>
<title>Test Etkinlik</title>
<link>https://etkinlik.io/etkinlik/1/test-etkinlik</link>
<description>Bir açıklama</description>
<pubDate>Mon, 20 Jul 2026 10:00:00 +0300</pubDate>
<category>Konser</category>
</item>
</channel></rss>"""


@respx.mock
async def test_fetch_feed_parses_items():
    respx.get("https://etkinlik.io/rss/sorgu").mock(return_value=httpx.Response(200, text=SAMPLE_RSS))
    items = await etkinlik_client.fetch_feed()
    assert items == [{
        "title": "Test Etkinlik",
        "link": "https://etkinlik.io/etkinlik/1/test-etkinlik",
        "description": "Bir açıklama",
        "pub_date": "Mon, 20 Jul 2026 10:00:00 +0300",
        "category": "Konser",
    }]


@respx.mock
async def test_fetch_feed_skips_items_without_link():
    xml = '<?xml version="1.0"?><rss><channel><item><title>Linksiz</title></item></channel></rss>'
    respx.get("https://etkinlik.io/rss/sorgu").mock(return_value=httpx.Response(200, text=xml))
    items = await etkinlik_client.fetch_feed()
    assert items == []
