from datetime import date

import httpx
import pytest
import respx

from modules.tefas import tefas_client


def test_parse_tarih_dotnet_format():
    # 1699963200000 ms = 2023-11-14T12:00:00Z (öğlen UTC — timezone farkları
    # yerel tarihi değiştirmesin diye kasıtlı olarak gün ortası seçildi)
    assert tefas_client._parse_tarih("/Date(1699963200000)/") == date(2023, 11, 14)


def test_parse_tarih_iso_format():
    assert tefas_client._parse_tarih("2026-07-20T00:00:00") == date(2026, 7, 20)


@respx.mock
async def test_fetch_fund_history_parses_response():
    respx.post("https://www.tefas.gov.tr/api/funds/fonFiyatBilgiGetir").mock(
        return_value=httpx.Response(200, json={"resultList": [
            {"fonKodu": "AFT", "fonUnvan": "Test Fon", "tarih": "/Date(1699963200000)/", "fiyat": 1.2345},
        ]})
    )
    rows = await tefas_client.fetch_fund_history("AFT")
    assert rows == [{"fund_code": "AFT", "title": "Test Fon", "day": date(2023, 11, 14), "price": 1.2345}]


@respx.mock
async def test_fetch_fund_history_skips_rows_without_tarih():
    respx.post("https://www.tefas.gov.tr/api/funds/fonFiyatBilgiGetir").mock(
        return_value=httpx.Response(200, json={"resultList": [{"fonKodu": "AFT", "fiyat": 1.0}]})
    )
    rows = await tefas_client.fetch_fund_history("AFT")
    assert rows == []
