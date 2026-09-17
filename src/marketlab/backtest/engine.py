from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from marketlab.backtest.metrics import backtest_metrics
from marketlab.strategies.base import Strategy


@dataclass
class BacktestResult:
    """In-memory research result. Not an execution blotter."""

    strategy_name: str
    symbol: str | None
    prices: pd.DataFrame
    position: pd.Series
    asset_returns: pd.Series
    strategy_returns: pd.Series
    equity: pd.Series
    metrics: dict

    @property
    def index(self) -> pd.DatetimeIndex:
        return self.strategy_returns.index


def run_backtest(
    strategy: Strategy,
    prices: pd.DataFrame,
    *,
    symbol: str | None = None,
    price_col: str = "close",
    lag_signals: bool = True,
) -> BacktestResult:
    """Vectorized long/flat (or short) backtest.

    Signals at bar t are applied to the *next* bar's return when ``lag_signals``
    is True, avoiding look-ahead on same-bar closes.
    """
    if prices.empty:
        raise ValueError("prices are empty")
    close = prices[price_col].astype(float)
    asset_returns = close.pct_change().fillna(0.0)
    raw = strategy.generate_signals(prices).reindex(prices.index).fillna(0.0).astype(float)
    position = raw.shift(1).fillna(0.0) if lag_signals else raw
    strategy_returns = (position * asset_returns).rename("strategy_return")
    equity = (1.0 + strategy_returns).cumprod().rename("equity")
    metrics = backtest_metrics(strategy_returns, position)
    return BacktestResult(
        strategy_name=getattr(strategy, "name", strategy.__class__.__name__),
        symbol=symbol,
        prices=prices,
        position=position.rename("position"),
        asset_returns=asset_returns.rename("asset_return"),
        strategy_returns=strategy_returns,
        equity=equity,
        metrics=metrics,
    )
