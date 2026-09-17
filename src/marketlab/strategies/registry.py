from __future__ import annotations

from collections.abc import Callable

from marketlab.exceptions import StrategyError
from marketlab.strategies.base import Strategy
from marketlab.strategies.buy_hold import BuyAndHold
from marketlab.strategies.momentum import MomentumTrend
from marketlab.strategies.sma_crossover import SmaCrossover

StrategyFactory = Callable[..., Strategy]

_REGISTRY: dict[str, StrategyFactory] = {
    "buy_hold": lambda **_: BuyAndHold(),
    "sma_crossover": lambda fast=20, slow=50, **_: SmaCrossover(fast=int(fast), slow=int(slow)),
    "momentum": lambda lookback=60, **_: MomentumTrend(lookback=int(lookback)),
}


def register_strategy(name: str, factory: StrategyFactory) -> None:
    _REGISTRY[name] = factory


def list_strategies() -> list[str]:
    return sorted(_REGISTRY)


def build_strategy(name: str, **params) -> Strategy:
    key = name.lower().strip()
    if key not in _REGISTRY:
        raise StrategyError(f"unknown strategy {name!r}. Built-in: {', '.join(list_strategies())}")
    return _REGISTRY[key](**params)
