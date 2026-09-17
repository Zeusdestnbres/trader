from marketlab.regimes.fetchers.base import RegimeFetcher
from marketlab.regimes.fetchers.election_years import ElectionYearFetcher
from marketlab.regimes.fetchers.nber import NberFetcher
from marketlab.regimes.fetchers.presidents import PresidentsFetcher
from marketlab.regimes.fetchers.registry import get_fetcher_class, list_fetchers, load_fetcher, register_fetcher
from marketlab.regimes.fetchers.vix import VixRegimeFetcher
from marketlab.regimes.calendar import RegimeCalendar, RegimePeriod, bundled_calendar_dir, load_calendar
from marketlab.regimes.compare import RegimeComparison, RegimeMetrics, compare_backtest_by_regime, compare_by_regime
from marketlab.regimes.slicer import RegimeSlicer

__all__ = [
    "RegimeCalendar",
    "RegimePeriod",
    "RegimeSlicer",
    "RegimeComparison",
    "RegimeMetrics",
    "compare_by_regime",
    "compare_backtest_by_regime",
    "load_calendar",
    "bundled_calendar_dir",
    "RegimeFetcher",
    "register_fetcher",
    "list_fetchers",
    "load_fetcher",
    "get_fetcher_class",
    "PresidentsFetcher",
    "NberFetcher",
    "VixRegimeFetcher",
    "ElectionYearFetcher",
]
