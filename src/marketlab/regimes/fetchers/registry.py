from __future__ import annotations

import importlib
from typing import Any

from marketlab.exceptions import FetcherError
from marketlab.regimes.fetchers.base import RegimeFetcher

_REGISTRY: dict[str, type[RegimeFetcher]] = {}


def register_fetcher(name: str | None = None):
    """Class decorator (or direct call) to publish a fetcher under a CLI name."""

    def deco(cls: type[RegimeFetcher]) -> type[RegimeFetcher]:
        key = (name or getattr(cls, "name", "") or cls.__name__).lower().strip()
        if not key:
            raise FetcherError("fetcher needs a name")
        cls.name = key
        _REGISTRY[key] = cls
        return cls

    return deco


def list_fetchers() -> dict[str, str]:
    return {name: getattr(cls, "description", "") or cls.__name__ for name, cls in sorted(_REGISTRY.items())}


def get_fetcher_class(name: str) -> type[RegimeFetcher]:
    key = name.lower().strip()
    if key not in _REGISTRY:
        raise FetcherError(
            f"unknown fetcher {name!r}. Built-in: {', '.join(list_fetchers()) or '(none)'}. "
            "Pass module:Class to load a custom fetcher."
        )
    return _REGISTRY[key]


def load_fetcher(spec: str, **kwargs: Any) -> RegimeFetcher:
    """Load by registry name, ``module:Class``, or ``module.Class``."""
    text = spec.strip()
    if text.lower() in _REGISTRY:
        return _REGISTRY[text.lower()](**kwargs)
    module_name = None
    cls_name = None
    if ":" in text:
        module_name, cls_name = text.split(":", 1)
    elif "." in text:
        module_name, cls_name = text.rsplit(".", 1)
    if not module_name or not cls_name:
        raise FetcherError(
            f"unknown fetcher {spec!r}. Built-in: {', '.join(list_fetchers())}. "
            "Custom: package.module:ClassName"
        )
    try:
        module = importlib.import_module(module_name)
        cls = getattr(module, cls_name)
    except (ImportError, AttributeError) as exc:
        raise FetcherError(f"could not import fetcher {spec!r}: {exc}") from exc
    if not isinstance(cls, type):
        raise FetcherError(f"{spec} is not a class")
    return cls(**kwargs)
