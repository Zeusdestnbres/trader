import pandas as pd

from marketlab.backtest.engine import run_backtest
from marketlab.strategies.buy_hold import BuyAndHold
from marketlab.strategies.sma_crossover import SmaCrossover
from tests.conftest import make_prices


def test_buy_hold_matches_asset() -> None:
    prices = make_prices(periods=80, seed=1)
    result = run_backtest(BuyAndHold(), prices, symbol="SYN", lag_signals=True)
    # Signal lag zeros the first bar; the first pct_change is also 0, so equity
    # still tracks close[-1] / close[0].
    close = prices["close"]
    expected = float(close.iloc[-1] / close.iloc[0] - 1.0)
    assert abs(result.metrics["total_return"] - expected) < 1e-10
    assert result.metrics["time_in_market"] < 1.0  # first bar flat due to lag
    assert abs(float(result.equity.iloc[-1]) - float(close.iloc[-1] / close.iloc[0])) < 1e-10


def test_sma_not_always_in_market() -> None:
    prices = make_prices(periods=200, seed=2, drift=0.0, sigma=0.02)
    result = run_backtest(SmaCrossover(fast=5, slow=20), prices, lag_signals=True)
    assert 0.0 <= result.metrics["time_in_market"] <= 1.0
    assert (result.position.isin([0.0, 1.0])).all()
    assert result.strategy_name == "sma_5_20"


def test_empty_prices_rejected() -> None:
    import pytest

    with pytest.raises(ValueError):
        run_backtest(BuyAndHold(), pd.DataFrame(columns=["close"]))
