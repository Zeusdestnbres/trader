from __future__ import annotations

from marketlab.exceptions import FetcherError
from marketlab.regimes.calendar import RegimeCalendar, load_calendar
from marketlab.regimes.fetchers.base import RegimeFetcher
from marketlab.regimes.fetchers.registry import register_fetcher


@register_fetcher("presidents")
class PresidentsFetcher(RegimeFetcher):
    """DEMO calendar: US presidential terms labeled by party.

    This is a sample of the generic regime format, not the product. Use any
    other YAML/CSV/JSON calendar or fetcher for research questions you care about.
    """

    name = "presidents"
    description = "Bundled US presidential party labels (DEMO calendar, not the product)"

    def fetch(self, *, allow_network: bool = True) -> RegimeCalendar:
        del allow_network
        try:
            cal = load_calendar("us_presidents")
        except Exception as exc:  # noqa: BLE001
            raise FetcherError(f"could not load demo presidential calendar: {exc}") from exc
        cal.source = cal.source or "bundled:us_presidents.yaml"
        return cal
