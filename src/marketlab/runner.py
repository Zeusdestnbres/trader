from __future__ import annotations

import pandas as pd

from marketlab.alerts.engine import AlertEngine
from marketlab.config import AppConfig
from marketlab.models import SymbolSnapshot
from marketlab.news.base import NewsProvider, StaticNewsProvider
from marketlab.news.yfinance_news import YFinanceNewsProvider
from marketlab.providers import build_provider
from marketlab.providers.base import PriceProvider


def build_provider_from_config(config: AppConfig) -> PriceProvider:
    return build_provider(config.provider, csv_data_dir=config.csv_data_dir)


def build_news_from_config(config: AppConfig) -> NewsProvider:
    if not config.news.enabled:
        return StaticNewsProvider()
    if config.provider == "csv":
        return StaticNewsProvider()
    return YFinanceNewsProvider()


def snapshot_symbol(
    symbol: str,
    provider: PriceProvider,
    news: NewsProvider,
    alerts: AlertEngine,
    *,
    news_limit: int,
    history_start: str | None = None,
) -> tuple[SymbolSnapshot, pd.DataFrame | None]:
    try:
        history = provider.history(symbol, start=history_start)
        try:
            quote = provider.quote(symbol)
        except Exception:
            from marketlab.providers.normalize import quote_from_history

            quote = quote_from_history(symbol, history)
        fired = alerts.check(symbol, quote, history)
        headlines = news.headlines(symbol, limit=news_limit) if news_limit else []
        snap = SymbolSnapshot(
            symbol=symbol,
            quote=quote,
            alerts=tuple(fired),
            headlines=tuple(headlines),
        )
        return snap, history
    except Exception as exc:  # noqa: BLE001 — per-symbol isolation
        return SymbolSnapshot(symbol=symbol, quote=None, error=str(exc)), None


def run_watchlist(
    config: AppConfig,
    *,
    provider: PriceProvider | None = None,
    news: NewsProvider | None = None,
    history_start: str | None = None,
) -> tuple[list[SymbolSnapshot], dict[str, pd.DataFrame]]:
    provider = provider or build_provider_from_config(config)
    news = news if news is not None else build_news_from_config(config)
    alerts = AlertEngine(config.alerts)
    snapshots: list[SymbolSnapshot] = []
    histories: dict[str, pd.DataFrame] = {}
    for symbol in config.watchlist:
        snap, hist = snapshot_symbol(
            symbol,
            provider,
            news,
            alerts,
            news_limit=config.news.per_symbol,
            history_start=history_start,
        )
        snapshots.append(snap)
        if hist is not None:
            histories[symbol] = hist
    return snapshots, histories
