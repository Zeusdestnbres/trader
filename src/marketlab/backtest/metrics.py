from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from marketlab.analysis.stats import max_drawdown, summary_stats


def backtest_metrics(
    strategy_returns: pd.Series,
    position: pd.Series,
    *,
    periods_per_year: int = 252,
) -> dict:
    rets = strategy_returns.dropna()
    if rets.empty:
        return {
            "n_bars": 0,
            "total_return": None,
            "cagr": None,
            "volatility": None,
            "max_drawdown": None,
            "sharpe": None,
            "win_rate": None,
            "time_in_market": None,
        }
    equity = (1.0 + rets).cumprod()
    in_mkt = position.reindex(rets.index).fillna(0.0).astype(float).abs() > 1e-12
    active = rets[in_mkt]
    wins = active[active > 0]
    win_rate = float(len(wins) / len(active)) if len(active) else None
    time_in_market = float(in_mkt.mean()) if len(in_mkt) else None
    stats = summary_stats(pd.DataFrame({"close": equity}), price_col="close", periods_per_year=periods_per_year)
    # summary_stats treats equity as a price; total_return/cagr/dd/sharpe still apply
    vol = float(rets.std(ddof=1)) * np.sqrt(periods_per_year) if len(rets) > 1 else None
    mean = float(rets.mean())
    std = float(rets.std(ddof=1)) if len(rets) > 1 else 0.0
    sharpe = float(mean / std * np.sqrt(periods_per_year)) if std else None
    return {
        "n_bars": int(len(rets)),
        "total_return": float(equity.iloc[-1] - 1.0),
        "cagr": stats["cagr"],
        "volatility": vol,
        "max_drawdown": max_drawdown(equity),
        "sharpe": sharpe,
        "win_rate": win_rate,
        "time_in_market": time_in_market,
        "start": str(rets.index[0].date()) if hasattr(rets.index[0], "date") else str(rets.index[0]),
        "end": str(rets.index[-1].date()) if hasattr(rets.index[-1], "date") else str(rets.index[-1]),
    }
