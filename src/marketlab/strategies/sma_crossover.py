from __future__ import annotations

import pandas as pd

from marketlab.strategies.base import Strategy, close_series


class SmaCrossover(Strategy):
    """Long when fast SMA > slow SMA, else flat. Classic research baseline."""

    def __init__(self, fast: int = 20, slow: int = 50) -> None:
        if fast <= 0 or slow <= 0 or fast >= slow:
            raise ValueError("need 0 < fast < slow")
        self.fast = fast
        self.slow = slow
        self.name = f"sma_{fast}_{slow}"

    def generate_signals(self, prices: pd.DataFrame) -> pd.Series:
        close = close_series(prices)
        fast = close.rolling(self.fast, min_periods=self.fast).mean()
        slow = close.rolling(self.slow, min_periods=self.slow).mean()
        long_ = (fast > slow).astype(float)
        long_ = long_.where(fast.notna() & slow.notna(), 0.0)
        return long_.rename("position")
