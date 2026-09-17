from __future__ import annotations

from datetime import date

import pandas as pd

from marketlab.exceptions import ProviderError
from marketlab.models import Quote
from marketlab.providers.base import PriceProvider
from marketlab.providers.normalize import normalize_ohlcv, parse_start_end, quote_from_history


class YFinanceProvider(PriceProvider):
    """Yahoo Finance via yfinance. Quotes and history only — no orders."""

    name = "yfinance"

    def history(
        self,
        symbol: str,
        *,
        start: date | str | None = None,
        end: date | str | None = None,
        interval: str = "1d",
    ) -> pd.DataFrame:
        try:
            import yfinance as yf
        except ImportError as exc:
            raise ProviderError("yfinance is not installed") from exc

        start_s, end_s = parse_start_end(start, end)
        ticker = yf.Ticker(symbol)
        kwargs: dict = {"interval": interval, "auto_adjust": False, "progress": False}
        if start_s or end_s:
            kwargs["start"] = start_s
            kwargs["end"] = end_s
        else:
            kwargs["period"] = "5y"

        try:
            raw = ticker.history(**kwargs)
        except TypeError:
            kwargs.pop("progress", None)
            raw = ticker.history(**kwargs)
        except Exception as exc:  # noqa: BLE001 — provider boundary
            raise ProviderError(f"yfinance history failed for {symbol}: {exc}") from exc

        return normalize_ohlcv(raw, symbol=symbol)

    def quote(self, symbol: str) -> Quote:
        try:
            import yfinance as yf
        except ImportError as exc:
            raise ProviderError("yfinance is not installed") from exc

        ticker = yf.Ticker(symbol)
        last = None
        prev = None
        currency = None
        try:
            info = getattr(ticker, "fast_info", None)
            if info is not None:
                last = _pick(info, "last_price", "lastPrice", "regular_market_price")
                prev = _pick(info, "previous_close", "previousClose")
                currency = _pick(info, "currency")
        except Exception:
            last = None

        if last is None:
            hist = self.history(symbol, start=None, end=None)
            q = quote_from_history(symbol, hist)
            return Quote(symbol=symbol, last=q.last, previous_close=q.previous_close, currency=currency, as_of=q.as_of)

        return Quote(
            symbol=symbol,
            last=_to_float(last),
            previous_close=_to_float(prev),
            currency=str(currency) if currency else None,
        )


def _pick(mapping, *keys):
    if mapping is None:
        return None
    getter = getattr(mapping, "get", None)
    for key in keys:
        try:
            if getter:
                value = getter(key)
            else:
                value = mapping[key]
        except Exception:
            continue
        if value is not None:
            return value
    return None


def _to_float(value) -> float | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
