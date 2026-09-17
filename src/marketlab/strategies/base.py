from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class Strategy(ABC):
    """Research strategy: maps OHLCV → target position in {-1, 0, +1} (or fractional).

    Signals are *not* orders. The backtester never routes them to a broker.
    """

    name: str = "strategy"

    @abstractmethod
    def generate_signals(self, prices: pd.DataFrame) -> pd.Series:
        """Return a Series aligned to ``prices.index`` (typically 0 or 1)."""


def close_series(prices: pd.DataFrame) -> pd.Series:
    if "close" not in prices.columns:
        raise KeyError("prices must include a 'close' column")
    return prices["close"].astype(float)
