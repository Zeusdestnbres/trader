from __future__ import annotations

import numpy as np
import pandas as pd


def extract_trend(
    prices: pd.DataFrame,
    *,
    price_col: str = "close",
    fast: int = 20,
    slow: int = 50,
    slope_window: int = 60,
) -> dict:
    """Lightweight trend extraction for reports (SMA stack + log-price slope)."""
    close = prices[price_col].astype(float).dropna()
    if close.empty:
        return {"state": "unknown", "sma_fast": None, "sma_slow": None, "log_slope": None}

    sma_fast = float(close.rolling(fast).mean().iloc[-1]) if len(close) >= fast else None
    sma_slow = float(close.rolling(slow).mean().iloc[-1]) if len(close) >= slow else None
    last = float(close.iloc[-1])
    log_slope = _log_slope(close, slope_window)

    if sma_fast is not None and sma_slow is not None:
        if last >= sma_fast >= sma_slow:
            state = "uptrend"
        elif last <= sma_fast <= sma_slow:
            state = "downtrend"
        else:
            state = "mixed"
    elif log_slope is not None:
        state = "uptrend" if log_slope > 0 else "downtrend" if log_slope < 0 else "flat"
    else:
        state = "unknown"

    hh_ll = _swing_bias(close)
    return {
        "state": state,
        "last": last,
        "sma_fast": sma_fast,
        "sma_slow": sma_slow,
        "log_slope": log_slope,
        "swing_bias": hh_ll,
        "fast": fast,
        "slow": slow,
        "slope_window": slope_window,
    }


def _log_slope(close: pd.Series, window: int) -> float | None:
    tail = close.tail(window)
    if len(tail) < 5:
        return None
    y = np.log(tail.to_numpy(dtype=float))
    if not np.isfinite(y).all():
        return None
    x = np.arange(len(y), dtype=float)
    slope, _intercept = np.polyfit(x, y, 1)
    return float(slope)


def _swing_bias(close: pd.Series, lookback: int = 20) -> str:
    if len(close) < lookback * 2:
        return "n/a"
    recent = close.iloc[-lookback:]
    prior = close.iloc[-lookback * 2 : -lookback]
    higher_high = bool(recent.max() > prior.max())
    higher_low = bool(recent.min() > prior.min())
    if higher_high and higher_low:
        return "higher_highs_higher_lows"
    if (not higher_high) and (not higher_low):
        return "lower_highs_lower_lows"
    return "mixed"
