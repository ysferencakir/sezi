"""Etkinlik başlığındaki anahtar kelimelere göre kategori çıkarımı.

Takvime etkinlik eklerken başlığa bu kelimelerden birini geçirmen yeterli
(büyük/küçük harf önemli değil). Eşleşme bulunamazsa "other" kategorisine düşer.
"""

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "work": [
        "staj", "mesai", "iş", "toplantı", "proje", "müşteri",
        "meeting", "work", "internship", "shift", "project", "client", "standup", "call",
    ],
    "class": [
        "ders", "sınav", "okul", "üniversite", "seminer", "sunum", "ödev",
        "class", "lecture", "exam", "school", "university", "seminar", "presentation", "homework", "lab",
    ],
    "deep_focus": [
        "derin odak", "odak",
        "deep focus", "focus", "deep work", "flow",
    ],
    "sport": [
        "spor", "antrenman", "koşu", "yüzme",
        "sport", "gym", "workout", "training", "run", "running", "swim", "swimming", "yoga", "pilates",
    ],
    "social": [
        "arkadaş", "buluşma", "sosyal", "parti", "davet", "yemek",
        "friend", "hangout", "social", "party", "invite", "dinner", "lunch", "coffee",
    ],
    "personal": [
        "randevu", "doktor", "diş", "berber", "kişisel",
        "appointment", "doctor", "dentist", "barber", "personal", "errand",
    ],
    "commute": [
        "servis", "shuttle", "ulaşım", "toplu taşıma", "dolmuş", "otobüs", "metro", "tramvay",
        "commute", "transit", "bus", "subway",
    ],
    "travel": [
        "seyahat", "uçuş", "yol", "tren",
        "travel", "trip", "flight", "train",
    ],
    "rest": [
        "dinlenme", "mola", "uyku",
        "rest", "break", "nap", "sleep",
    ],
}


def categorize(title: str) -> str:
    """Etkinlik başlığını CATEGORY_KEYWORDS ile eşleştirip kategori döndürür."""
    lowered = (title or "").lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return category
    return "other"
