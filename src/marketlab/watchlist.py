from __future__ import annotations


def parse_symbols(text: str | None, fallback: list[str]) -> list[str]:
    if not text:
        return list(fallback)
    symbols = [s.strip().upper() for s in text.split(",") if s.strip()]
    return symbols or list(fallback)
