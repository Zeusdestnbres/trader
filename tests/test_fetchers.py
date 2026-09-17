from datetime import date

import pandas as pd

from marketlab.providers.csv_provider import CsvPriceProvider
from marketlab.regimes.fetchers.election_years import ElectionYearFetcher
from marketlab.regimes.fetchers.nber import NberFetcher, calendar_from_fred_usrec
from marketlab.regimes.fetchers.presidents import PresidentsFetcher
from marketlab.regimes.fetchers.registry import list_fetchers, load_fetcher
from marketlab.regimes.fetchers.vix import VixRegimeFetcher
from tests.conftest import write_ohlcv_csv


FRED_SAMPLE = """DATE,USREC
2006-01-01,0
2007-11-01,0
2007-12-01,1
2008-06-01,1
2009-06-01,1
2009-07-01,0
2010-01-01,0
"""


def test_registry_includes_real_and_demo_fetchers() -> None:
    names = list_fetchers()
    assert "presidents" in names
    assert "nber" in names
    assert "vix" in names
    assert "election_years" in names
    assert "DEMO" in names["presidents"]


def test_nber_offline_and_fred_parser() -> None:
    cal = NberFetcher().fetch(allow_network=False)
    assert "recession" in cal.unique_labels()
    assert "expansion" in cal.unique_labels()
    assert cal.labels_at(date(2008, 3, 1)) == ["recession"]
    parsed = calendar_from_fred_usrec(FRED_SAMPLE)
    assert parsed.labels_at(date(2008, 1, 15)) == ["recession"]
    assert parsed.labels_at(date(2006, 6, 1)) == ["expansion"]


def test_presidents_fetcher_demo() -> None:
    cal = PresidentsFetcher().fetch(allow_network=False)
    assert "Republican" in cal.unique_labels()


def test_election_year_fetcher() -> None:
    cal = ElectionYearFetcher(start_year=2020, end_year=2021).fetch()
    assert cal.labels_at(date(2020, 7, 4)) == ["election_year"]
    assert cal.labels_at(date(2021, 7, 4)) == ["non_election_year"]


def test_vix_hysteresis(tmp_path) -> None:
    idx = pd.bdate_range("2020-01-01", periods=10)
    close = pd.Series([10, 12, 14, 30, 22, 20, 18, 12, 10, 11], index=idx, dtype=float)
    frame = pd.DataFrame(
        {"open": close, "high": close, "low": close, "close": close, "volume": 1.0},
        index=idx,
    )
    write_ohlcv_csv(tmp_path / "VIX.csv", frame)
    provider = CsvPriceProvider(tmp_path)
    cal = VixRegimeFetcher(provider, symbol="VIX", high=25, low=15, start=None).fetch()
    labels = [cal.labels_at(ts.date())[0] for ts in idx]
    assert labels[0] == "low_vol"
    assert labels[3] == "high_vol"
    assert labels[5] == "high_vol"  # hysteresis: 20 is between 15 and 25
    assert labels[7] == "low_vol"


def test_load_fetcher_by_name() -> None:
    fetcher = load_fetcher("election_years", start_year=2016, end_year=2016)
    cal = fetcher.fetch()
    assert cal.labels_at(date(2016, 1, 2)) == ["election_year"]
