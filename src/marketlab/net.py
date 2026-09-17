from __future__ import annotations

from urllib.request import Request, urlopen

from marketlab.exceptions import FetcherError

USER_AGENT = "marketlab-research/0.1 (analysis-only; never-trades)"


def fetch_text(url: str, *, timeout: float = 20.0) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(req, timeout=timeout) as resp:  # nosec B310 — caller passes https URLs
            raw = resp.read()
    except Exception as exc:  # noqa: BLE001
        raise FetcherError(f"download failed for {url}: {exc}") from exc
    return raw.decode("utf-8", errors="replace")
