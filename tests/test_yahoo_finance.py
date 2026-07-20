import httpx
import respx

from modules.stocks import yahoo_finance


@respx.mock
async def test_fetch_last_daily_bar_picks_latest_non_null_close():
    body = {
        "chart": {"result": [{
            "timestamp": [1700000000, 1700086400],
            "indicators": {"quote": [{
                "open": [10.0, 11.0],
                "high": [10.5, 11.5],
                "low": [9.5, 10.5],
                "close": [10.2, None],
                "volume": [1000, 2000],
            }]},
        }]}
    }
    respx.get(url__regex=r".*/v8/finance/chart/.*").mock(return_value=httpx.Response(200, json=body))
    bar = await yahoo_finance.fetch_last_daily_bar("XU100.IS")
    assert bar["close"] == 10.2
    assert bar["open"] == 10.0


@respx.mock
async def test_fetch_last_daily_bar_returns_none_when_no_result():
    respx.get(url__regex=r".*/v8/finance/chart/.*").mock(
        return_value=httpx.Response(200, json={"chart": {"result": None}})
    )
    bar = await yahoo_finance.fetch_last_daily_bar("BILINMEYEN.IS")
    assert bar is None
