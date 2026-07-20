import httpx
import respx

from core.config import settings
from modules.watchlog import tmdb_client


@respx.mock
async def test_search_returns_first_movie_or_tv_result(monkeypatch):
    monkeypatch.setattr(settings, "tmdb_api_key", "test-key")
    respx.get("https://api.themoviedb.org/3/search/multi").mock(
        return_value=httpx.Response(200, json={"results": [
            {"media_type": "person", "id": 1, "name": "Someone"},
            {"media_type": "tv", "id": 42, "name": "The Mentalist", "overview": "A show.",
             "poster_path": "/x.jpg", "first_air_date": "2008-09-23"},
        ]})
    )
    result = await tmdb_client.search("The Mentalist")
    assert result == {
        "tmdb_id": 42,
        "media_type": "tv",
        "title": "The Mentalist",
        "overview": "A show.",
        "poster_path": "/x.jpg",
        "release_date": "2008-09-23",
    }


async def test_search_returns_none_without_api_key(monkeypatch):
    monkeypatch.setattr(settings, "tmdb_api_key", "")
    result = await tmdb_client.search("anything")
    assert result is None


@respx.mock
async def test_search_returns_none_when_only_person_results(monkeypatch):
    monkeypatch.setattr(settings, "tmdb_api_key", "test-key")
    respx.get("https://api.themoviedb.org/3/search/multi").mock(
        return_value=httpx.Response(200, json={"results": [{"media_type": "person", "id": 1}]})
    )
    result = await tmdb_client.search("Someone")
    assert result is None
