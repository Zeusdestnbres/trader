from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import yaml

from marketlab.exceptions import ConfigError

DEFAULT_WATCHLIST = ["SPY", "QQQ", "AAPL", "MSFT"]


@dataclass
class AlertConfig:
    pct_change: float = 3.0
    sma_cross: bool = True
    fast: int = 20
    slow: int = 50


@dataclass
class NewsConfig:
    enabled: bool = True
    per_symbol: int = 3


@dataclass
class RegimeConfig:
    calendar: str = "us_presidents"
    group_by: str = "label"
    calendars_dir: str = "./calendars"


@dataclass
class BacktestConfig:
    strategy: str = "sma_crossover"
    fast: int = 20
    slow: int = 50
    lookback: int = 60
    start: str | None = "2015-01-01"
    end: str | None = None


@dataclass
class AppConfig:
    watchlist: list[str] = field(default_factory=lambda: list(DEFAULT_WATCHLIST))
    provider: str = "yfinance"
    csv_data_dir: str = "./data/prices"
    alerts: AlertConfig = field(default_factory=AlertConfig)
    news: NewsConfig = field(default_factory=NewsConfig)
    regimes: RegimeConfig = field(default_factory=RegimeConfig)
    backtest: BacktestConfig = field(default_factory=BacktestConfig)
    config_path: Path | None = None

    def with_watchlist(self, symbols: list[str]) -> AppConfig:
        return replace(self, watchlist=symbols)


def _as_list(value: Any) -> list[str]:
    if value is None:
        return list(DEFAULT_WATCHLIST)
    if isinstance(value, str):
        return [s.strip().upper() for s in value.split(",") if s.strip()]
    if isinstance(value, list):
        return [str(s).strip().upper() for s in value if str(s).strip()]
    raise ConfigError(f"watchlist must be a list or comma-separated string, got {type(value)}")


def load_config(path: str | Path | None = None) -> AppConfig:
    """Load YAML config. Missing file → defaults (useful on first run)."""
    if path is None:
        for candidate in (Path("marketlab.yaml"), Path("config.yaml"), Path("config.example.yaml")):
            if candidate.exists():
                path = candidate
                break
    if path is None:
        return AppConfig()

    cfg_path = Path(path)
    if not cfg_path.exists():
        raise ConfigError(f"config file not found: {cfg_path}")

    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ConfigError("config root must be a mapping")

    alerts_raw = raw.get("alerts") or {}
    news_raw = raw.get("news") or {}
    regimes_raw = raw.get("regimes") or {}
    bt_raw = raw.get("backtest") or {}

    return AppConfig(
        watchlist=_as_list(raw.get("watchlist")),
        provider=str(raw.get("provider", "yfinance")).lower(),
        csv_data_dir=str(raw.get("csv_data_dir", "./data/prices")),
        alerts=AlertConfig(
            pct_change=float(alerts_raw.get("pct_change", 3.0)),
            sma_cross=bool(alerts_raw.get("sma_cross", True)),
            fast=int(alerts_raw.get("fast", 20)),
            slow=int(alerts_raw.get("slow", 50)),
        ),
        news=NewsConfig(
            enabled=bool(news_raw.get("enabled", True)),
            per_symbol=int(news_raw.get("per_symbol", 3)),
        ),
        regimes=RegimeConfig(
            calendar=str(regimes_raw.get("calendar", "us_presidents")),
            group_by=str(regimes_raw.get("group_by", "label")),
            calendars_dir=str(regimes_raw.get("calendars_dir", "./calendars")),
        ),
        backtest=BacktestConfig(
            strategy=str(bt_raw.get("strategy", "sma_crossover")),
            fast=int(bt_raw.get("fast", 20)),
            slow=int(bt_raw.get("slow", 50)),
            lookback=int(bt_raw.get("lookback", 60)),
            start=bt_raw.get("start", "2015-01-01"),
            end=bt_raw.get("end"),
        ),
        config_path=cfg_path,
    )
