from datetime import date

from marketlab.regimes.calendar import RegimeCalendar, RegimePeriod
from marketlab.regimes.fetchers.base import RegimeFetcher
from marketlab.regimes.fetchers.registry import list_fetchers, load_fetcher, register_fetcher


@register_fetcher("unit_test_source")
class _ToyFetcher(RegimeFetcher):
    description = "example plugin used by tests"

    def fetch(self, *, allow_network: bool = True) -> RegimeCalendar:
        del allow_network
        return RegimeCalendar(
            name="unit_test_source",
            periods=[RegimePeriod(date(2020, 1, 1), date(2020, 12, 31), "on")],
            source="unit-test",
        )


def test_register_and_load_custom_fetcher() -> None:
    assert "unit_test_source" in list_fetchers()
    cal = load_fetcher("unit_test_source").fetch()
    assert cal.labels_at(date(2020, 6, 1)) == ["on"]
