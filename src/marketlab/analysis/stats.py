from __future__ import annotations

import numpy as np
import pandas as pd


def summary_stats(prices: pd.DataFrame, *, price_col: str = "close", periods_per_year: int = 252) -> dict:
    close = prices[price_col].astype(float).dropna()
    rets = close.pct_change().dropna()
    if close.empty or rets.empty:
        return {
            "n_bars": int(len(close)),
            "total_return": None,
            "cagr": None,
            "volatility": None,
            "max_drawdown": None,
            "sharpe": None,
            "start": None,
            "end": None,
        }

    equity = close / close.iloc[0]
    total_return = float(equity.iloc[-1] - 1.0)
    dd = max_drawdown(equity)
    vol = float(rets.std(ddof=1)) * np.sqrt(periods_per_year) if len(rets) > 1 else None
    sharpe = _sharpe(rets, periods_per_year)
    years = max((close.index[-1] - close.index[0]).days / 365.25, 1e-9)
    cagr = float(equity.iloc[-1] ** (1 / years) - 1) if years > 0 and equity.iloc[-1] > 0 else None
    return {
        "n_bars": int(len(close)),
        "total_return": total_return,
        "cagr": cagr,
        "volatility": vol,
        "max_drawdown": dd,
        "sharpe": sharpe,
        "start": str(close.index[0].date()) if hasattr(close.index[0], "date") else str(close.index[0]),
        "end": str(close.index[-1].date()) if hasattr(close.index[-1], "date") else str(close.index[-1]),
        "last": float(close.iloc[-1]),
    }


def max_drawdown(equity: pd.Series) -> float | None:
    if equity.empty:
        return None
    peak = equity.cummax()
    dd = equity / peak - 1.0
    return float(dd.min())


def _sharpe(returns: pd.Series, periods_per_year: int) -> float | None:
    if len(returns) < 2:
        return None
    std = float(returns.std(ddof=1))
    if std == 0:
        return None
    return float(returns.mean() / std * np.sqrt(periods_per_year))
