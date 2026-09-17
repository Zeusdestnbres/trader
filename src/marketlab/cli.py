"""CLI for research-only market analysis. Never places trades."""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from marketlab import __version__
from marketlab.config import AppConfig, load_config
from marketlab.disclaimer import DISCLAIMER, NO_BROKER_NOTE
from marketlab.watchlist import parse_symbols


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "cmd", None):
        parser.print_help()
        print("\n" + DISCLAIMER, file=sys.stderr)
        return 1
    try:
        config = load_config(args.config)
        if getattr(args, "watchlist", None):
            config = config.with_watchlist(parse_symbols(args.watchlist, config.watchlist))
        if getattr(args, "provider", None):
            config.provider = args.provider
        if getattr(args, "csv_data_dir", None):
            config.csv_data_dir = args.csv_data_dir
        return args.handler(args, config)
    except KeyboardInterrupt:
        print("\nStopped.", file=sys.stderr)
        return 0
    except Exception as exc:  # noqa: BLE001 — CLI boundary
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="marketlab",
        description="Market analysis and strategy research (no orders, no broker APIs).",
        epilog=DISCLAIMER,
    )
    parser.add_argument("--version", action="version", version=f"marketlab {__version__}")
    parser.add_argument("-c", "--config", help="YAML config path (default: marketlab.yaml if present)")
    parser.add_argument("--watchlist", help="Comma-separated symbols, overriding config")
    parser.add_argument("--provider", choices=("yfinance", "csv"), help="Price provider")
    parser.add_argument("--csv-data-dir", help="Directory of SYMBOL.csv files when --provider csv")
    sub = parser.add_subparsers(dest="cmd")

    p_watch = sub.add_parser("watch", help="Loop quotes, news, and research alerts")
    p_watch.add_argument("--interval", type=int, default=60, help="Seconds between refreshes")
    p_watch.set_defaults(handler=cmd_watch)

    p_once = sub.add_parser("once", help="Single watchlist snapshot")
    p_once.set_defaults(handler=cmd_once)

    p_report = sub.add_parser("report", help="Write an analysis report (stats + trend)")
    p_report.add_argument("--symbol", help="Restrict to one symbol")
    p_report.add_argument("--out", help="Write markdown to this path instead of stdout")
    p_report.set_defaults(handler=cmd_report)

    p_bt = sub.add_parser("backtest", help="Run a strategy backtest (research only)")
    p_bt.add_argument("--symbol", help="Symbol (default: first watchlist name)")
    p_bt.add_argument("--strategy", help="buy_hold | sma_crossover | momentum")
    p_bt.add_argument("--fast", type=int)
    p_bt.add_argument("--slow", type=int)
    p_bt.add_argument("--lookback", type=int)
    p_bt.add_argument("--start")
    p_bt.add_argument("--end")
    p_bt.set_defaults(handler=cmd_backtest)

    p_rg = sub.add_parser(
        "regimes",
        help="Compare a strategy's returns sliced by a labeled calendar (any labels)",
    )
    p_rg.add_argument("--symbol")
    p_rg.add_argument("--strategy")
    p_rg.add_argument("--fast", type=int)
    p_rg.add_argument("--slow", type=int)
    p_rg.add_argument("--lookback", type=int)
    p_rg.add_argument("--start")
    p_rg.add_argument("--end")
    p_rg.add_argument("--calendar", help="Path or bundled name (us_presidents, nber_recessions, example_custom)")
    p_rg.add_argument("--fetcher", help="Fetcher name or module:Class (nber, vix, election_years, presidents)")
    p_rg.add_argument("--group-by", help="label | category | metadata.<key>")
    p_rg.add_argument("--offline", action="store_true", help="Do not hit the network for fetchers")
    p_rg.add_argument("--list-calendars", action="store_true")
    p_rg.add_argument("--list-fetchers", action="store_true")
    p_rg.add_argument("--out", help="Write text report to this path")
    p_rg.set_defaults(handler=cmd_regimes)
    return parser


def cmd_watch(args: argparse.Namespace, config: AppConfig) -> int:
    print(NO_BROKER_NOTE)
    print(DISCLAIMER)
    print()
    interval = max(5, int(args.interval))
    while True:
        _print_snapshot(config)
        time.sleep(interval)
    return 0  # pragma: no cover


def cmd_once(args: argparse.Namespace, config: AppConfig) -> int:
    del args
    print(NO_BROKER_NOTE)
    _print_snapshot(config)
    return 0


def cmd_report(args: argparse.Namespace, config: AppConfig) -> int:
    from marketlab.analysis.reports import render_report
    from marketlab.runner import run_watchlist

    if args.symbol:
        config = config.with_watchlist([args.symbol.upper()])
    snapshots, histories = run_watchlist(config)
    text = render_report(snapshots, histories)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"Wrote {args.out}")
    else:
        print(text)
    return 0


def cmd_backtest(args: argparse.Namespace, config: AppConfig) -> int:
    result = _run_bt(args, config)
    m = result.metrics
    print(NO_BROKER_NOTE)
    print(f"strategy: {result.strategy_name}  symbol: {result.symbol}")
    print(f"window:   {m.get('start')} → {m.get('end')}  bars: {m.get('n_bars')}")
    print(f"return:   {_pct(m.get('total_return'))}  CAGR: {_pct(m.get('cagr'))}")
    print(f"vol:      {_pct(m.get('volatility'))}  max DD: {_pct(m.get('max_drawdown'))}")
    print(f"sharpe*:  {_num(m.get('sharpe'))}  win rate: {_pct(m.get('win_rate'))}")
    print(f"time in market: {_pct(m.get('time_in_market'))}")
    print()
    print(DISCLAIMER)
    return 0


def cmd_regimes(args: argparse.Namespace, config: AppConfig) -> int:
    import marketlab.regimes.fetchers  # noqa: F401 — register built-ins
    from marketlab.regimes.calendar import load_calendar
    from marketlab.regimes.compare import compare_by_regime
    from marketlab.regimes.fetchers.registry import list_fetchers, load_fetcher

    extra = [config.regimes.calendars_dir]
    if args.list_calendars:
        _print_calendars(extra)
        return 0
    if args.list_fetchers:
        print("Built-in fetchers (research labels only):")
        for name, desc in list_fetchers().items():
            print(f"  {name:16} {desc}")
        print()
        print("Custom: --fetcher my_package.module:MyFetcher")
        print("Presidency (presidents / us_presidents) is a DEMO calendar, not the product.")
        return 0

    calendar = None
    if args.fetcher:
        from marketlab.runner import build_provider_from_config

        provider = build_provider_from_config(config)
        kwargs = {}
        spec = args.fetcher
        if spec.lower() in {"vix"}:
            kwargs["provider"] = provider
        calendar = load_fetcher(spec, **kwargs).fetch(allow_network=not args.offline)
    else:
        ref = args.calendar or config.regimes.calendar
        calendar = load_calendar(ref, extra_dirs=extra)

    result_bt = _run_bt(args, config)
    group_by = args.group_by or config.regimes.group_by
    from marketlab.strategies.registry import build_strategy

    # Re-run via compare_by_regime API (strategy + calendar + prices)
    strategy = build_strategy(
        args.strategy or config.backtest.strategy,
        fast=args.fast or config.backtest.fast,
        slow=args.slow or config.backtest.slow,
        lookback=args.lookback or config.backtest.lookback,
    )
    comparison = compare_by_regime(
        strategy,
        calendar,
        result_bt.prices,
        group_by=group_by,
        symbol=result_bt.symbol,
    )
    text = comparison.render()
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"Wrote {args.out}")
    else:
        print(text)
    return 0


def _run_bt(args: argparse.Namespace, config: AppConfig):
    from marketlab.backtest.engine import run_backtest
    from marketlab.runner import build_provider_from_config
    from marketlab.strategies.registry import build_strategy

    symbol = (args.symbol or config.watchlist[0]).upper()
    start = args.start if getattr(args, "start", None) else config.backtest.start
    end = args.end if getattr(args, "end", None) else config.backtest.end
    strategy = build_strategy(
        args.strategy or config.backtest.strategy,
        fast=args.fast or config.backtest.fast,
        slow=args.slow or config.backtest.slow,
        lookback=args.lookback or config.backtest.lookback,
    )
    provider = build_provider_from_config(config)
    prices = provider.history(symbol, start=start, end=end)
    return run_backtest(strategy, prices, symbol=symbol)


def _print_snapshot(config: AppConfig) -> None:
    from marketlab.runner import run_watchlist

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"=== {now} ===")
    snapshots, _hist = run_watchlist(config)
    for snap in snapshots:
        if snap.error:
            print(f"  {snap.symbol:8} ERROR {snap.error}")
            continue
        q = snap.quote
        last = f"{q.last:.4f}" if q and q.last is not None else "n/a"
        pct = f"{q.pct_change:+.2%}" if q and q.pct_change is not None else ""
        print(f"  {snap.symbol:8} {last:>12} {pct:>8}")
        for alert in snap.alerts:
            print(f"           ALERT [{alert.kind}] {alert.message}")
        for h in snap.headlines:
            print(f"           NEWS  {h.title}")
    print()


def _print_calendars(extra_dirs: list[str]) -> None:
    from marketlab.regimes.calendar import iter_bundled_calendar_files

    print("Bundled sample calendars:")
    for path in iter_bundled_calendar_files():
        note = "  (DEMO only)" if path.stem == "us_presidents" else ""
        print(f"  {path.stem:20} {path}{note}")
    print()
    for folder in extra_dirs:
        p = Path(folder)
        if not p.exists():
            print(f"User calendars dir {p} does not exist yet — create it and drop YAML/CSV/JSON.")
            continue
        files = [f for f in p.iterdir() if f.suffix.lower() in {".yaml", ".yml", ".json", ".csv"}]
        print(f"User calendars in {p}:")
        if not files:
            print("  (empty)")
        for f in files:
            print(f"  {f.stem:20} {f}")
    print()
    print("Load with: marketlab regimes --calendar nber_recessions")
    print("        or marketlab regimes --calendar C:\\path\\to\\my_regimes.yaml")


def _pct(value) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.2%}"


def _num(value) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.3f}"


if __name__ == "__main__":
    raise SystemExit(main())
