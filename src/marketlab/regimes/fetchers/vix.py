from __future__ import annotations

import pandas as pd

from marketlab.exceptions import FetcherError
from marketlab.providers.base import PriceProvider
from marketlab.regimes.calendar import RegimeCalendar
from marketlab.regimes.fetchers.base import RegimeFetcher, periods_from_labeled_series
from marketlab.regimes.fetchers.registry import register_fetcher


@register_fetcher("vix")
class VixRegimeFetcher(RegimeFetcher):
    """Derive high/low volatility regimes from a VIX-like series (default ``^VIX``).

    Uses hysteresis: enter ``high_vol`` at ``high``, leave to ``low_vol`` at ``low``.
    Requires a price provider (yfinance or CSV). This is a derived label set, not
    a causal claim about future returns.
    """

    name = "vix"
    description = "High/low vol regimes from VIX (hysteresis thresholds, market-data derived)"

    def __init__(
        self,
        provider: PriceProvider | None = None,
        *,
        symbol: str = "^VIX",
        high: float = 25.0,
        low: float = 15.0,
        start: str | None = "1990-01-01",
    ) -> None:
        self.provider = provider
        self.symbol = symbol
        self.high = float(high)
        self.low = float(low)
        self.start = start
        if self.low >= self.high:
            raise FetcherError("VIX low threshold must be < high threshold")

    def fetch(self, *, allow_network: bool = True) -> RegimeCalendar:
        del allow_network
        if self.provider is None:
            raise FetcherError("VixRegimeFetcher requires a price provider")
        history = self.provider.history(self.symbol, start=self.start)
        if history.empty or "close" not in history.columns:
            raise FetcherError(f"no VIX history for {self.symbol}")
        labels = _hysteresis_labels(history["close"].astype(float), high=self.high, low=self.low)
        periods = periods_from_labeled_series(labels, category="vix")
        if not periods:
            raise FetcherError("VIX series produced no regimes")
        return RegimeCalendar(
            name="vix_regimes",
            periods=periods,
            source=f"{self.symbol} via {getattr(self.provider, 'name', 'provider')}",
            description=f"Hysteresis high>={self.high:g} / low<={self.low:g} on {self.symbol} close.",
        )


def _hysteresis_labels(close: pd.Series, *, high: float, low: float) -> pd.Series:
    state = "mid_vol"
    out: list[str] = []
    for value in close.tolist():
        if pd.isna(value):
            out.append(state)
            continue
        if value >= high:
            state = "high_vol"
        elif value <= low:
            state = "low_vol"
        elif state == "mid_vol":
            state = "mid_vol"
        out.append(state)
    return pd.Series(out, index=close.index, name="vix_regime")
