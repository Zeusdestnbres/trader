from marketlab.analysis.stats import summary_stats
from marketlab.analysis.trends import extract_trend
from marketlab.config import load_config
from tests.conftest import make_prices


def test_summary_and_trend() -> None:
    prices = make_prices(periods=120, seed=8, drift=0.002)
    stats = summary_stats(prices)
    assert stats["n_bars"] == 120
    assert stats["total_return"] is not None
    trend = extract_trend(prices, fast=10, slow=20, slope_window=30)
    assert trend["state"] in {"uptrend", "downtrend", "mixed", "unknown"}
    assert trend["log_slope"] is not None


def test_load_example_config(tmp_path) -> None:
    path = tmp_path / "c.yaml"
    path.write_text("watchlist: [SPY, QQQ]\nprovider: yfinance\n", encoding="utf-8")
    cfg = load_config(path)
    assert cfg.watchlist == ["SPY", "QQQ"]
    assert cfg.provider == "yfinance"


def test_default_config_without_file(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    cfg = load_config(None)
    assert "SPY" in cfg.watchlist
