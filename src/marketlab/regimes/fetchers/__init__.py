"""Pluggable regime fetchers. Import this package to populate the registry."""

from marketlab.regimes.fetchers.base import RegimeFetcher, periods_from_labeled_series
from marketlab.regimes.fetchers.election_years import ElectionYearFetcher
from marketlab.regimes.fetchers.nber import NberFetcher
from marketlab.regimes.fetchers.presidents import PresidentsFetcher
from marketlab.regimes.fetchers.registry import get_fetcher_class, list_fetchers, load_fetcher, register_fetcher
from marketlab.regimes.fetchers.vix import VixRegimeFetcher

__all__ = [
    "RegimeFetcher",
    "periods_from_labeled_series",
    "register_fetcher",
    "list_fetchers",
    "load_fetcher",
    "get_fetcher_class",
    "PresidentsFetcher",
    "NberFetcher",
    "VixRegimeFetcher",
    "ElectionYearFetcher",
]
