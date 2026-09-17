from __future__ import annotations

from datetime import date

import pandas as pd

from marketlab.exceptions import ProviderError
from marketlab.models import Quote
from marketlab.providers.base import OHLCV_COLUMNS


def normalize_ohlcv(frame: pd.DataFrame, *, symbol: str) -> pd.DataFrame:
    if frame is None or frame.empty:
        raise ProviderError(f"no price history for {symbol}")

    df = frame.copy()
    if isinstance(df.columns, pd.MultiIndex):
        # yfinance may return (field, ticker)
        level0 = df.columns.get_level_values(0)
        if symbol in set(df.columns.get_level_values(-1)):
            df = df.xs(symbol, axis=1, level=-1)
        else:
            df.columns = level0

    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    rename = {"adj_close": "adj_close", "adjclose": "adj_close"}
    df = df.rename(columns=rename)
    if "close" not in df.columns:
        if "adj_close" in df.columns:
            df["close"] = df["adj_close"]
        else:
            raise ProviderError(f"{symbol}: history missing a close column: {list(df.columns)}")

    for col in OHLCV_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA if col != "close" else df["close"]

    df.index = pd.to_datetime(df.index)
    if getattr(df.index, "tz", None) is not None:
        df.index = df.index.tz_convert("UTC").tz_localize(None)
    df = df.sort_index()
    df = df[~df.index.duplicated(keep="last")]
    return df[list(OHLCV_COLUMNS)]


def quote_from_history(symbol: str, history: pd.DataFrame) -> Quote:
    if history.empty:
        raise ProviderError(f"no bars to quote for {symbol}")
    last = history.iloc[-1]
    prev = history.iloc[-2]["close"] if len(history) > 1 else None
    ts = history.index[-1]
    as_of = ts.to_pydatetime() if hasattr(ts, "to_pydatetime") else None
    return Quote(
        symbol=symbol,
        last=float(last["close"]),
        previous_close=float(prev) if prev is not None and pd.notna(prev) else None,
        as_of=as_of,
    )


def parse_start_end(
    start: date | str | None,
    end: date | str | None,
) -> tuple[str | None, str | None]:
    def _fmt(v: date | str | None) -> str | None:
        if v is None:
            return None
        if isinstance(v, date):
            return v.isoformat()
        return str(v)

    return _fmt(start), _fmt(end)
