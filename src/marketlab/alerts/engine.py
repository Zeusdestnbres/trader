from __future__ import annotations

import pandas as pd

from marketlab.config import AlertConfig
from marketlab.models import Alert, Quote


class AlertEngine:
    """Research alerts (console/report). These never trigger orders."""

    def __init__(self, config: AlertConfig | None = None) -> None:
        self.config = config or AlertConfig()

    def check(self, symbol: str, quote: Quote | None, history: pd.DataFrame | None) -> list[Alert]:
        alerts: list[Alert] = []
        threshold = abs(self.config.pct_change) / 100.0
        pct = quote.pct_change if quote else None
        if pct is None and history is not None and len(history) >= 2:
            close = history["close"]
            prev, last = float(close.iloc[-2]), float(close.iloc[-1])
            if prev:
                pct = (last / prev) - 1.0
        if pct is not None and abs(pct) >= threshold:
            alerts.append(
                Alert(
                    symbol=symbol,
                    kind="pct_change",
                    message=f"{symbol} moved {pct:.2%} vs previous close (threshold {self.config.pct_change:.2f}%)",
                    details={"pct_change": pct, "threshold": threshold},
                )
            )

        if self.config.sma_cross and history is not None:
            cross = _sma_cross_alert(symbol, history, self.config.fast, self.config.slow)
            if cross:
                alerts.append(cross)
        return alerts


def _sma_cross_alert(symbol: str, history: pd.DataFrame, fast: int, slow: int) -> Alert | None:
    if "close" not in history.columns or len(history) < slow + 1:
        return None
    close = history["close"].astype(float)
    f = close.rolling(fast).mean()
    s = close.rolling(slow).mean()
    if pd.isna(f.iloc[-1]) or pd.isna(s.iloc[-1]) or pd.isna(f.iloc[-2]) or pd.isna(s.iloc[-2]):
        return None
    prev_above = bool(f.iloc[-2] > s.iloc[-2])
    now_above = bool(f.iloc[-1] > s.iloc[-1])
    if prev_above == now_above:
        return None
    direction = "bullish" if now_above else "bearish"
    return Alert(
        symbol=symbol,
        kind="sma_cross",
        message=f"{symbol} {fast}/{slow} SMA cross ({direction}) — research signal, not an order",
        details={"fast": fast, "slow": slow, "direction": direction},
    )
