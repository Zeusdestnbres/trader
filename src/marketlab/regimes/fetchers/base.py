from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, timedelta

import pandas as pd

from marketlab.regimes.calendar import RegimeCalendar, RegimePeriod
from marketlab.regimes.slicer import as_date


class RegimeFetcher(ABC):
    """Turn a public or derived data source into a ``RegimeCalendar``.

    Fetchers are research helpers. They do not trade and they do not imply
    that a label caused returns.
    """

    name: str
    description: str = ""

    @abstractmethod
    def fetch(self, *, allow_network: bool = True) -> RegimeCalendar:
        raise NotImplementedError


def periods_from_labeled_series(
    series: pd.Series,
    *,
    category: str | None = None,
    metadata: dict | None = None,
    end_inclusive_month: bool = False,
) -> list[RegimePeriod]:
    """Collapse consecutive equal labels into periods.

    ``series`` must have a DatetimeIndex. Empty / NA labels are skipped as breaks.
    """
    if series.empty:
        return []
    s = series.copy()
    s.index = pd.to_datetime(s.index)
    s = s.sort_index()
    periods: list[RegimePeriod] = []
    run_label: str | None = None
    run_start = None
    prev_ts = None

    def _close(end_ts, lab: str) -> None:
        end_d = as_date(end_ts)
        if end_inclusive_month:
            end_d = _month_end(end_d)
        periods.append(
            RegimePeriod(
                start=as_date(run_start),
                end=end_d,
                label=str(lab),
                category=category,
                metadata=dict(metadata or {}),
            )
        )

    for ts, raw in s.items():
        if raw is None or (isinstance(raw, float) and pd.isna(raw)) or str(raw).strip() == "":
            if run_label is not None and prev_ts is not None:
                _close(prev_ts, run_label)
                run_label = None
                run_start = None
            prev_ts = ts
            continue
        lab = str(raw)
        if run_label is None:
            run_label = lab
            run_start = ts
        elif lab != run_label:
            _close(prev_ts, run_label)
            run_label = lab
            run_start = ts
        prev_ts = ts
    if run_label is not None and run_start is not None and prev_ts is not None:
        _close(prev_ts, run_label)
    return periods


def _month_end(day: date) -> date:
    if day.month == 12:
        return date(day.year, 12, 31)
    return date(day.year, day.month + 1, 1) - timedelta(days=1)
