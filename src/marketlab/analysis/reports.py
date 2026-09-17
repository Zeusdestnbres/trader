from __future__ import annotations

from datetime import datetime, timezone

from marketlab.analysis.stats import summary_stats
from marketlab.analysis.trends import extract_trend
from marketlab.disclaimer import DISCLAIMER
from marketlab.models import SymbolSnapshot


def render_report(
    snapshots: list[SymbolSnapshot],
    histories: dict,
    *,
    title: str = "MarketLab research report",
) -> str:
    lines = [
        f"# {title}",
        "",
        f"_Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_",
        "",
        DISCLAIMER,
        "",
        "## Watchlist snapshot",
        "",
    ]
    for snap in snapshots:
        if snap.error:
            lines.append(f"- **{snap.symbol}**: error — {snap.error}")
            continue
        q = snap.quote
        pct = ""
        if q and q.pct_change is not None:
            pct = f" ({q.pct_change:+.2%})"
        last = f"{q.last:.4f}" if q and q.last is not None else "n/a"
        lines.append(f"- **{snap.symbol}**: last {last}{pct}")
        for alert in snap.alerts:
            lines.append(f"  - ALERT `{alert.kind}`: {alert.message}")
        for h in snap.headlines:
            lines.append(f"  - NEWS: {h.title}")

    lines += ["", "## Per-symbol stats and trend", ""]
    for symbol, hist in histories.items():
        if hist is None or getattr(hist, "empty", True):
            lines.append(f"### {symbol}")
            lines.append("No history.")
            lines.append("")
            continue
        stats = summary_stats(hist)
        trend = extract_trend(hist)
        lines.append(f"### {symbol}")
        lines.append("")
        lines.append(f"- Window: {stats['start']} → {stats['end']} ({stats['n_bars']} bars)")
        lines.append(f"- Total return: {_pct(stats['total_return'])}")
        lines.append(f"- CAGR: {_pct(stats['cagr'])}")
        lines.append(f"- Volatility (ann.): {_pct(stats['volatility'])}")
        lines.append(f"- Max drawdown: {_pct(stats['max_drawdown'])}")
        lines.append(f"- Sharpe-ish (rf=0): {_num(stats['sharpe'])}")
        lines.append(
            f"- Trend: **{trend['state']}** "
            f"(SMA {trend['fast']}/{trend['slow']}, slope { _num(trend['log_slope']) }, "
            f"swings {trend['swing_bias']})"
        )
        lines.append("")

    lines += ["", "---", DISCLAIMER, ""]
    return "\n".join(lines)


def _pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2%}"


def _num(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.4f}"
