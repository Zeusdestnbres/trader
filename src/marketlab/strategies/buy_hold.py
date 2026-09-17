from __future__ import annotations

import pandas as pd

from marketlab.strategies.base import Strategy, close_series


class BuyAndHold(Strategy):
    name = "buy_hold"

    def generate_signals(self, prices: pd.DataFrame) -> pd.Series:
        close = close_series(prices)
        return pd.Series(1.0, index=close.index, name="position")
