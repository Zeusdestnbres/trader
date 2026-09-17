from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from marketlab.exceptions import ProviderError
from marketlab.models import Quote
from marketlab.providers.base import PriceProvider
from marketlab.providers.normalize import normalize_ohlcv, quote_from_history


class CsvPriceProvider(PriceProvider):
    """Local OHLCV CSVs named ``{SYMBOL}.csv`` with a date column and OHLCV fields."""

    name = "csv"

    def __init__(self, data_dir: str | Path) -> None:
        self.data_dir = Path(data_dir)

    def history(
        self,
        symbol: str,
        *,
        start: date | str | None = None,
        end: date | str | None = None,
        interval: str = "1d",
    ) -> pd.DataFrame:
        del interval  # daily files only
        path = self._path(symbol)
        if not path.exists():
            raise ProviderError(f"CSV not found for {symbol}: {path}")
        df = pd.read_csv(path)
        date_col = _date_column(df)
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.set_index(date_col)
        out = normalize_ohlcv(df, symbol=symbol)
        if start:
            out = out[out.index >= pd.Timestamp(start)]
        if end:
            out = out[out.index <= pd.Timestamp(end)]
        if out.empty:
            raise ProviderError(f"no rows for {symbol} in requested window")
        return out

    def quote(self, symbol: str) -> Quote:
        return quote_from_history(symbol, self.history(symbol))

    def _path(self, symbol: str) -> Path:
        return self.data_dir / f"{symbol.upper()}.csv"


def _date_column(df: pd.DataFrame) -> str:
    for name in ("date", "Date", "datetime", "Datetime", "timestamp"):
        if name in df.columns:
            return name
    raise ProviderError(f"CSV missing a date column; have {list(df.columns)}")
