import pandas as pd

from marketlab.alerts.engine import AlertEngine
from marketlab.config import AlertConfig
from marketlab.models import Quote


def test_pct_change_alert() -> None:
    engine = AlertEngine(AlertConfig(pct_change=2.0, sma_cross=False))
    quote = Quote(symbol="AAA", last=103.0, previous_close=100.0)
    alerts = engine.check("AAA", quote, None)
    assert any(a.kind == "pct_change" for a in alerts)


def test_no_alert_small_move() -> None:
    engine = AlertEngine(AlertConfig(pct_change=5.0, sma_cross=False))
    quote = Quote(symbol="AAA", last=101.0, previous_close=100.0)
    assert engine.check("AAA", quote, None) == []


def test_sma_cross_alert() -> None:
    idx = pd.bdate_range("2020-01-01", periods=20)
    # Downtrend, then a last-bar spike so fast SMA crosses above slow on the final print.
    values = [100 - i for i in range(19)] + [200]
    close = pd.Series(values, index=idx, dtype=float)
    hist = pd.DataFrame({"close": close})
    engine = AlertEngine(AlertConfig(pct_change=999.0, sma_cross=True, fast=3, slow=8))
    alerts = engine.check("XYZ", None, hist)
    assert any(a.kind == "sma_cross" for a in alerts)
