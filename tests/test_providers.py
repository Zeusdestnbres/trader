from marketlab.providers import build_provider
from marketlab.providers.csv_provider import CsvPriceProvider
from tests.conftest import make_prices, write_ohlcv_csv


def test_csv_provider_history_and_quote(tmp_path) -> None:
    prices = make_prices(periods=30, seed=9)
    write_ohlcv_csv(tmp_path / "QQQ.csv", prices)
    provider = CsvPriceProvider(tmp_path)
    hist = provider.history("QQQ")
    assert len(hist) == 30
    assert "close" in hist.columns
    q = provider.quote("qqq")
    assert q.last == float(hist["close"].iloc[-1])
    sliced = provider.history("QQQ", start=str(hist.index[5].date()), end=str(hist.index[10].date()))
    assert len(sliced) <= 7


def test_build_provider_rejects_broker_names() -> None:
    import pytest

    with pytest.raises(ValueError):
        build_provider("trading212")
