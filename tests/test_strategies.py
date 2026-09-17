import pandas as pd
import pytest

from marketlab.strategies.momentum import MomentumTrend
from marketlab.strategies.registry import build_strategy, list_strategies
from marketlab.strategies.sma_crossover import SmaCrossover
from tests.conftest import make_prices


def test_registry() -> None:
    names = list_strategies()
    assert "buy_hold" in names
    assert "sma_crossover" in names
    assert "momentum" in names
    s = build_strategy("sma_crossover", fast=10, slow=30)
    assert s.name == "sma_10_30"


def test_sma_long_when_fast_above_slow() -> None:
    idx = pd.bdate_range("2020-01-01", periods=30)
    close = pd.Series(range(1, 31), index=idx, dtype=float)
    prices = pd.DataFrame({"close": close})
    sig = SmaCrossover(fast=3, slow=5).generate_signals(prices)
    assert sig.iloc[:4].sum() == 0
    assert sig.iloc[-1] == 1.0


def test_momentum_flat_until_lookback() -> None:
    prices = make_prices(periods=40, seed=3)
    sig = MomentumTrend(lookback=10).generate_signals(prices)
    assert (sig.iloc[:9] == 0).all()


def test_sma_rejects_bad_windows() -> None:
    with pytest.raises(ValueError):
        SmaCrossover(fast=50, slow=20)
