from __future__ import annotations

from abc import ABC, abstractmethod

from marketlab.models import Headline


class NewsProvider(ABC):
    """Read-only headlines. Never used to send orders."""

    @abstractmethod
    def headlines(self, symbol: str, *, limit: int = 5) -> list[Headline]:
        raise NotImplementedError


class StaticNewsProvider(NewsProvider):
    """Test/offline stub."""

    def __init__(self, items: dict[str, list[Headline]] | None = None) -> None:
        self.items = items or {}

    def headlines(self, symbol: str, *, limit: int = 5) -> list[Headline]:
        return list(self.items.get(symbol.upper(), []))[:limit]
