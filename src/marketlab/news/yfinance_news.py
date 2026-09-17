from __future__ import annotations

from datetime import datetime, timezone

from marketlab.models import Headline
from marketlab.news.base import NewsProvider


class YFinanceNewsProvider(NewsProvider):
    def headlines(self, symbol: str, *, limit: int = 5) -> list[Headline]:
        try:
            import yfinance as yf
        except ImportError:
            return []

        try:
            raw = yf.Ticker(symbol).news or []
        except Exception:
            return []

        out: list[Headline] = []
        for item in raw[: max(limit * 2, limit)]:
            title = _title(item)
            if not title:
                continue
            out.append(
                Headline(
                    symbol=symbol,
                    title=title,
                    publisher=_nested(item, "publisher", "content", "provider", "displayName"),
                    url=_nested(item, "link", "url", "content", "canonicalUrl", "url"),
                    published=_published(item),
                )
            )
            if len(out) >= limit:
                break
        return out


def _title(item: dict) -> str:
    if not isinstance(item, dict):
        return ""
    content = item.get("content") if isinstance(item.get("content"), dict) else {}
    return str(
        item.get("title")
        or content.get("title")
        or item.get("headline")
        or ""
    ).strip()


def _nested(item: dict, *keys):
    cur = item
    for key in keys:
        if not isinstance(cur, dict):
            return None
        if key in cur:
            cur = cur[key]
        else:
            return None
    return cur if not isinstance(cur, dict) else None


def _published(item: dict) -> datetime | None:
    content = item.get("content") if isinstance(item.get("content"), dict) else {}
    value = (
        item.get("providerPublishTime")
        or item.get("provider_publish_time")
        or content.get("pubDate")
        or content.get("displayTime")
    )
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
