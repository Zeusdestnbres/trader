from datetime import date

import pandas as pd

from marketlab.backtest.engine import BacktestResult
from marketlab.regimes.calendar import RegimeCalendar, RegimePeriod
from marketlab.regimes.compare import compare_backtest_by_regime, compare_by_regime
from marketlab.strategies.buy_hold import BuyAndHold


def _prices() -> pd.DataFrame:
    idx = pd.bdate_range("2020-01-01", periods=6)
    close = pd.Series([100.0, 101.0, 102.01, 103.0301, 101.0, 98.0], index=idx)
    return pd.DataFrame(
        {"open": close, "high": close, "low": close, "close": close, "volume": 1.0},
        index=idx,
    )


def test_compare_by_regime_public_api() -> None:
    prices = _prices()
    cal = RegimeCalendar(
        name="halves",
        periods=[
            RegimePeriod(date(2020, 1, 1), date(2020, 1, 3), "early"),
            RegimePeriod(date(2020, 1, 4), date(2020, 12, 31), "late"),
        ],
    )
    comparison = compare_by_regime(BuyAndHold(), cal, prices, symbol="TEST")
    assert comparison.calendar_name == "halves"
    assert "early" in comparison.by_label
    assert "late" in comparison.by_label
    assert comparison.overall is not None
    assert comparison.overall.n_bars == 6
    table = comparison.table()
    assert "total_return" in table.columns
    text = comparison.render()
    assert "not trading advice" in text.lower() or "Not trading advice" in text or "not causation" in text.lower()


def test_compare_metrics_known_returns() -> None:
    idx = pd.bdate_range("2020-01-01", periods=6)
    strategy_returns = pd.Series([0.01, 0.01, 0.01, -0.01, -0.01, -0.01], index=idx)
    position = pd.Series(1.0, index=idx)
    prices = pd.DataFrame({"close": 100.0}, index=idx)
    result = BacktestResult(
        strategy_name="toy",
        symbol="X",
        prices=prices,
        position=position,
        asset_returns=strategy_returns,
        strategy_returns=strategy_returns,
        equity=(1 + strategy_returns).cumprod(),
        metrics={},
    )
    cal = RegimeCalendar(
        name="ab",
        periods=[
            RegimePeriod(idx[0].date(), idx[2].date(), "A"),
            RegimePeriod(idx[3].date(), idx[5].date(), "B"),
        ],
    )
    comparison = compare_backtest_by_regime(result, cal, include_unlabeled=False)
    a = comparison.by_label["A"]
    b = comparison.by_label["B"]
    assert a.n_bars == 3
    assert b.n_bars == 3
    assert abs(a.total_return - ((1.01**3) - 1)) < 1e-12
    assert abs(b.total_return - ((0.99**3) - 1)) < 1e-12
    assert a.win_rate == 1.0
    assert b.win_rate == 0.0
    assert a.time_in_market == 1.0
    assert a.n_periods == 1


def test_overlap_counts_in_each_label() -> None:
    idx = pd.bdate_range("2020-01-01", periods=4)
    rets = pd.Series([0.01, 0.01, 0.01, 0.01], index=idx)
    result = BacktestResult(
        strategy_name="toy",
        symbol="X",
        prices=pd.DataFrame({"close": 100.0}, index=idx),
        position=pd.Series(1.0, index=idx),
        asset_returns=rets,
        strategy_returns=rets,
        equity=(1 + rets).cumprod(),
        metrics={},
    )
    cal = RegimeCalendar(
        name="overlap",
        periods=[
            RegimePeriod(idx[0].date(), idx[-1].date(), "all"),
            RegimePeriod(idx[0].date(), idx[1].date(), "first_two"),
        ],
    )
    comparison = compare_backtest_by_regime(result, cal, include_unlabeled=False)
    assert comparison.by_label["all"].n_bars == 4
    assert comparison.by_label["first_two"].n_bars == 2
