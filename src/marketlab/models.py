from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


@dataclass(frozen=True)
class Quote:
    symbol: str
    last: float | None
    previous_close: float | None = None
    currency: str | None = None
    as_of: datetime | None = None

    @property
    def pct_change(self) -> float | None:
        if self.last is None or self.previous_close in (None, 0):
            return None
        return (self.last / self.previous_close) - 1.0


@dataclass(frozen=True)
class Headline:
    symbol: str
    title: str
    publisher: str | None = None
    url: str | None = None
    published: datetime | None = None


@dataclass(frozen=True)
class Alert:
    symbol: str
    kind: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SymbolSnapshot:
    symbol: str
    quote: Quote | None
    alerts: tuple[Alert, ...] = ()
    headlines: tuple[Headline, ...] = ()
    error: str | None = None
