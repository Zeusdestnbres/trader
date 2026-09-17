from __future__ import annotations

from datetime import date

from marketlab.regimes.calendar import RegimeCalendar, RegimePeriod
from marketlab.regimes.fetchers.base import RegimeFetcher
from marketlab.regimes.fetchers.registry import register_fetcher


@register_fetcher("election_years")
class ElectionYearFetcher(RegimeFetcher):
    """US presidential election-year vs other years (computed, no download).

    Another example of a generic label set: years divisible by 4 vs the rest.
    """

    name = "election_years"
    description = "US presidential election year vs non-election year (computed)"

    def __init__(self, *, start_year: int = 1928, end_year: int | None = None) -> None:
        self.start_year = start_year
        self.end_year = end_year or date.today().year + 4

    def fetch(self, *, allow_network: bool = True) -> RegimeCalendar:
        del allow_network
        periods: list[RegimePeriod] = []
        for year in range(self.start_year, self.end_year + 1):
            label = "election_year" if year % 4 == 0 else "non_election_year"
            periods.append(
                RegimePeriod(
                    start=date(year, 1, 1),
                    end=date(year, 12, 31),
                    label=label,
                    category="us_election",
                    metadata={"year": str(year)},
                )
            )
        return RegimeCalendar(
            name="us_election_years",
            periods=periods,
            source="computed: year % 4 == 0",
            description="Calendar years labeled election_year (presidential) vs non_election_year.",
        )
