from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

import pandas as pd

from marketlab.models import Quote

OHLCV_COLUMNS = ("open", "high", "low", "close", "volume")


class PriceProvider(ABC):
    """Read-only market data. Implementations must not submit orders."""

    name: str

    @abstractmethod
    def history(
        self,
        symbol: str,
        *,
        start: date | str | None = None,
        end: date | str | None = None,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """Return OHLCV with a DatetimeIndex and lowercase columns including ``close``."""

    @abstractmethod
    def quote(self, symbol: str) -> Quote:
        """Latest snapshot. May fall back to the last history bar."""
