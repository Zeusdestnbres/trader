from __future__ import annotations

import pandas as pd

from marketlab.strategies.base import Strategy, close_series


class MomentumTrend(Strategy):
    """Long when close is above its lookback SMA (simple trend filter)."""

    def __init__(self, lookback: int = 60) -> None:
        if lookback < 2:
            raise ValueError("lookback must be >= 2")
        self.lookback = lookback
        self.name = f"momentum_{lookback}"

    def generate_signals(self, prices: pd.DataFrame) -> pd.Series:
        close = close_series(prices)
        sma = close.rolling(self.lookback, min_periods=self.lookback).mean()
        sig = (close > sma).astype(float)
        return sig.where(sma.notna(), 0.0).rename("position")
