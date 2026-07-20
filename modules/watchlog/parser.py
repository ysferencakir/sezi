import re

# Sırayla denenir, ilk eşleşen kazanır. Hepsi "başlık" + (varsa) sezon/bölüm yakalar.
_PATTERNS = [
    # "The Mentalist S2E5"
    re.compile(r"^(?P<title>.+?)\s+S(?P<season>\d{1,2})E(?P<episode>\d{1,3})\s*$", re.IGNORECASE),
    # "The Mentalist 2x05"
    re.compile(r"^(?P<title>.+?)\s+(?P<season>\d{1,2})x(?P<episode>\d{1,3})\s*$", re.IGNORECASE),
    # "Breaking Bad sezon 3 bölüm 7"
    re.compile(r"^(?P<title>.+?)\s+sezon\s*(?P<season>\d+)\s*,?\s*b[öo]l[üu]m\s*(?P<episode>\d+)\s*$", re.IGNORECASE),
    # "The Mentalist 5. bölüm" (sezon belirtilmemiş)
    re.compile(r"^(?P<title>.+?)\s+(?P<episode>\d+)\.?\s*b[öo]l[üu]m\s*$", re.IGNORECASE),
]


def parse_watch_text(text: str) -> dict:
    """Serbest metinden başlık + (varsa) sezon/bölüm çıkarır. Hiçbiri eşleşmezse
    tüm metin başlık kabul edilir (film ya da bölüm belirtilmemiş dizi)."""
    text = text.strip()
    for pattern in _PATTERNS:
        match = pattern.match(text)
        if not match:
            continue
        groups = match.groupdict()
        return {
            "title": groups["title"].strip(),
            "season": int(groups["season"]) if groups.get("season") else None,
            "episode": int(groups["episode"]) if groups.get("episode") else None,
        }
    return {"title": text, "season": None, "episode": None}
