import pytest

from modules.watchlog.parser import parse_watch_text


@pytest.mark.parametrize("text,expected", [
    ("The Mentalist 5. bölüm", {"title": "The Mentalist", "season": None, "episode": 5}),
    ("the mentalist 5.bölüm", {"title": "the mentalist", "season": None, "episode": 5}),
    ("The Mentalist S2E5", {"title": "The Mentalist", "season": 2, "episode": 5}),
    ("The Mentalist 2x05", {"title": "The Mentalist", "season": 2, "episode": 5}),
    ("Breaking Bad sezon 3 bölüm 7", {"title": "Breaking Bad", "season": 3, "episode": 7}),
    ("Inception", {"title": "Inception", "season": None, "episode": None}),
])
def test_parse_watch_text(text, expected):
    assert parse_watch_text(text) == expected
