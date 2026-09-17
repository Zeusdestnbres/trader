from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from marketlab.analysis.stats import max_drawdown
from marketlab.backtest.engine import BacktestResult, run_backtest
from marketlab.disclaimer import DISCLAIMER
from marketlab.regimes.calendar import RegimeCalendar
from marketlab.regimes.slicer import UNLABELED, RegimeSlicer
from marketlab.strategies.base import Strategy


@dataclass(frozen=True)
class RegimeMetrics:
    label: str
    n_bars: int
    n_periods: int
    total_return: float | None
    max_drawdown: float | None
    sharpe: float | None
    win_rate: float | None
    time_in_market: float | None

    def as_dict(self) -> dict:
        return {
            "label": self.label,
            "n_bars": self.n_bars,
            "n_periods": self.n_periods,
            "total_return": self.total_return,
            "max_drawdown": self.max_drawdown,
            "sharpe": self.sharpe,
            "win_rate": self.win_rate,
            "time_in_market": self.time_in_market,
        }


@dataclass
class RegimeComparison:
    calendar_name: str
    group_by: str
    strategy_name: str
    symbol: str | None
    by_label: dict[str, RegimeMetrics]
    overall: RegimeMetrics | None = None
    disclaimer: str = DISCLAIMER
    notes: list[str] = field(default_factory=list)

    def table(self) -> pd.DataFrame:
        rows = [m.as_dict() for m in self.by_label.values()]
        if self.overall:
            rows.append(self.overall.as_dict())
        return pd.DataFrame(rows)

    def render(self) -> str:
        lines = [
            f"# Regime comparison — {self.strategy_name}"
            + (f" / {self.symbol}" if self.symbol else ""),
            "",
            f"Calendar: **{self.calendar_name}**  |  group_by: `{self.group_by}`",
            "",
            self.disclaimer,
            "",
        ]
        df = self.table()
        if df.empty:
            lines.append("No overlapping bars.")
        else:
            show = df.copy()
            for col in ("total_return", "max_drawdown", "win_rate", "time_in_market"):
                if col in show:
                    show[col] = show[col].map(lambda v: "" if v is None or (isinstance(v, float) and np.isnan(v)) else f"{v:.2%}")
            if "sharpe" in show:
                show["sharpe"] = show["sharpe"].map(
                    lambda v: "" if v is None or (isinstance(v, float) and np.isnan(v)) else f"{v:.3f}"
                )
            lines.append(show.to_string(index=False))
        for note in self.notes:
            lines += ["", note]
        return "\n".join(lines) + "\n"


def compare_by_regime(
    strategy: Strategy,
    calendar: RegimeCalendar,
    prices: pd.DataFrame,
    *,
    slicer: RegimeSlicer | None = None,
    group_by: str = "label",
    symbol: str | None = None,
    price_col: str = "close",
    periods_per_year: int = 252,
) -> RegimeComparison:
    """Run ``strategy`` on ``prices`` and slice metrics by calendar labels.

    Bars that fall in overlapping periods are counted under every matching label.
    """
    result = run_backtest(strategy, prices, symbol=symbol, price_col=price_col)
    return compare_backtest_by_regime(
        result,
        calendar,
        slicer=slicer,
        group_by=group_by,
        periods_per_year=periods_per_year,
    )


def compare_backtest_by_regime(
    result: BacktestResult,
    calendar: RegimeCalendar,
    *,
    slicer: RegimeSlicer | None = None,
    group_by: str = "label",
    periods_per_year: int = 252,
    include_unlabeled: bool = True,
) -> RegimeComparison:
    slicer = slicer or RegimeSlicer(calendar, group_by=group_by)
    returns = result.strategy_returns.astype(float)
    position = result.position.reindex(returns.index).fillna(0.0).astype(float)
    tags = slicer.tags_index(returns.index)

    labels = calendar.unique_labels(slicer.group_by)
    by_label: dict[str, RegimeMetrics] = {}
    for label in labels:
        mask = tags.map(lambda xs, lab=label: lab in xs)
        by_label[label] = _metrics_for(
            label,
            returns[mask],
            position[mask],
            n_periods=_count_runs(mask.to_numpy()),
            periods_per_year=periods_per_year,
        )

    unlabeled_mask = tags.map(lambda xs: len(xs) == 0)
    if include_unlabeled and bool(unlabeled_mask.any()):
        by_label[UNLABELED] = _metrics_for(
            UNLABELED,
            returns[unlabeled_mask],
            position[unlabeled_mask],
            n_periods=_count_runs(unlabeled_mask.to_numpy()),
            periods_per_year=periods_per_year,
        )

    overall = _metrics_for(
        "_all",
        returns,
        position,
        n_periods=1,
        periods_per_year=periods_per_year,
    )
    notes = [
        "Pooled by label: non-contiguous windows that share a label are concatenated in time order.",
        "Overlapping periods contribute the same bar to every matching label.",
        DISCLAIMER,
    ]
    return RegimeComparison(
        calendar_name=calendar.name,
        group_by=slicer.group_by,
        strategy_name=result.strategy_name,
        symbol=result.symbol,
        by_label=by_label,
        overall=overall,
        notes=notes,
    )


def _metrics_for(
    label: str,
    returns: pd.Series,
    position: pd.Series,
    *,
    n_periods: int,
    periods_per_year: int,
) -> RegimeMetrics:
    rets = returns.dropna()
    n = int(len(rets))
    if n == 0:
        return RegimeMetrics(label, 0, n_periods, None, None, None, None, None)
    equity = (1.0 + rets).cumprod()
    total = float(equity.iloc[-1] - 1.0)
    dd = max_drawdown(equity)
    std = float(rets.std(ddof=1)) if n > 1 else 0.0
    sharpe = float(rets.mean() / std * np.sqrt(periods_per_year)) if std else None
    in_mkt = position.reindex(rets.index).fillna(0.0).abs() > 1e-12
    active = rets[in_mkt]
    win_rate = float((active > 0).mean()) if len(active) else None
    time_in_market = float(in_mkt.mean())
    return RegimeMetrics(
        label=label,
        n_bars=n,
        n_periods=n_periods,
        total_return=total,
        max_drawdown=dd,
        sharpe=sharpe,
        win_rate=win_rate,
        time_in_market=time_in_market,
    )


def _count_runs(mask: np.ndarray) -> int:
    if mask.size == 0:
        return 0
    m = mask.astype(bool)
    if not m.any():
        return 0
    padded = np.concatenate([[False], m])
    return int(np.sum(padded[1:] & ~padded[:-1]))
