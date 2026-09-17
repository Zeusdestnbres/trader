from __future__ import annotations

import io
from calendar import monthrange
from datetime import date, timedelta

import pandas as pd

from marketlab.exceptions import FetcherError
from marketlab.net import fetch_text
from marketlab.regimes.calendar import RegimeCalendar, RegimePeriod
from marketlab.regimes.fetchers.base import RegimeFetcher, periods_from_labeled_series
from marketlab.regimes.fetchers.registry import register_fetcher

# Official NBER peak–trough months (inclusive), commonly cited cycle dates.
# Source: https://www.nber.org/research/data/us-business-cycle-expansions-and-contractions
NBER_RECESSIONS: list[tuple[date, date]] = [
    (date(1929, 8, 1), date(1933, 3, 31)),
    (date(1937, 5, 1), date(1938, 6, 30)),
    (date(1945, 2, 1), date(1945, 10, 31)),
    (date(1948, 11, 1), date(1949, 10, 31)),
    (date(1953, 7, 1), date(1954, 5, 31)),
    (date(1957, 8, 1), date(1958, 4, 30)),
    (date(1960, 4, 1), date(1961, 2, 28)),
    (date(1969, 12, 1), date(1970, 11, 30)),
    (date(1973, 11, 1), date(1975, 3, 31)),
    (date(1980, 1, 1), date(1980, 7, 31)),
    (date(1981, 7, 1), date(1982, 11, 30)),
    (date(1990, 7, 1), date(1991, 3, 31)),
    (date(2001, 3, 1), date(2001, 11, 30)),
    (date(2007, 12, 1), date(2009, 6, 30)),
    (date(2020, 2, 1), date(2020, 4, 30)),
]

FRED_USREC_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=USREC"


@register_fetcher("nber")
class NberFetcher(RegimeFetcher):
    """US business-cycle regimes: recession vs expansion.

    Tries FRED series USREC (monthly 0/1). On network failure, uses the bundled
    NBER peak/trough dates. Labels are ``recession`` / ``expansion``.
    """

    name = "nber"
    description = "NBER recession vs expansion (FRED USREC, bundled fallback)"

    def __init__(self, *, url: str = FRED_USREC_URL) -> None:
        self.url = url

    def fetch(self, *, allow_network: bool = True) -> RegimeCalendar:
        if allow_network:
            try:
                text = fetch_text(self.url)
                cal = calendar_from_fred_usrec(text)
                cal.source = self.url
                return cal
            except (FetcherError, ValueError, OSError):
                pass
        return bundled_nber_calendar()


def bundled_nber_calendar() -> RegimeCalendar:
    return RegimeCalendar(
        name="nber_cycles",
        periods=_periods_from_recessions(NBER_RECESSIONS),
        source="nber.org (curated peak/trough; fallback when FRED is unavailable)",
        description="US recession vs expansion windows from NBER cycle dates.",
    )


def _periods_from_recessions(recessions: list[tuple[date, date]]) -> list[RegimePeriod]:
    periods: list[RegimePeriod] = []
    prev_end: date | None = None
    for start, end in recessions:
        if prev_end is not None:
            exp_start = prev_end + timedelta(days=1)
            exp_end = start - timedelta(days=1)
            if exp_start <= exp_end:
                periods.append(
                    RegimePeriod(start=exp_start, end=exp_end, label="expansion", category="nber")
                )
        elif start > date(1929, 1, 1):
            periods.append(
                RegimePeriod(start=date(1929, 1, 1), end=start - timedelta(days=1), label="expansion", category="nber")
            )
        periods.append(RegimePeriod(start=start, end=end, label="recession", category="nber"))
        prev_end = end
    if prev_end is not None:
        periods.append(
            RegimePeriod(start=prev_end + timedelta(days=1), end=None, label="expansion", category="nber")
        )
    return periods


def calendar_from_fred_usrec(csv_text: str) -> RegimeCalendar:
    """Parse FRED USREC CSV (DATE,USREC with 0/1 monthly observations)."""
    buf = io.StringIO(csv_text)
    df = pd.read_csv(buf)
    cols = {c.lower(): c for c in df.columns}
    date_col = cols.get("date") or cols.get("observation_date")
    value_col = None
    for key, orig in cols.items():
        if key != "date" and key != "observation_date":
            value_col = orig
            break
    if date_col is None or value_col is None:
        raise ValueError(f"USREC CSV missing date/value columns: {list(df.columns)}")
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])
    values = pd.to_numeric(df[value_col], errors="coerce")
    labels = values.map(lambda v: "recession" if pd.notna(v) and int(v) == 1 else "expansion")
    series = pd.Series(labels.to_numpy(), index=pd.DatetimeIndex(df[date_col]))
    periods = periods_from_labeled_series(series, category="nber", end_inclusive_month=True)
    if not periods:
        raise ValueError("USREC CSV produced no periods")
    # Open-ended last expansion if the series ends at 0
    if periods[-1].label == "expansion":
        last = periods[-1]
        periods[-1] = RegimePeriod(
            start=last.start,
            end=None,
            label=last.label,
            category=last.category,
            metadata=dict(last.metadata),
        )
    return RegimeCalendar(
        name="nber_cycles",
        periods=periods,
        source="FRED USREC",
        description="US recession vs expansion from FRED monthly recession indicator.",
    )


def month_end(year: int, month: int) -> date:
    return date(year, month, monthrange(year, month)[1])
