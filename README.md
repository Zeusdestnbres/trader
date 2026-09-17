# MarketLab

Research-only market analysis and strategy backtesting for Windows (and anywhere Python runs).

**This program never places trades.** There is no broker integration and no Trading 212 (or any other) order API. It reads prices, headlines, and labeled calendars, then prints reports. That is the whole product.

Regime statistics are **descriptive**. **Correlation is not causation.** A label (party, recession, high-VIX, your own tag) coinciding with returns does not mean the label caused those returns. Nothing here is trading advice, an offer to transact, or a recommendation to buy or sell any security.

---

## What it does

| CLI | Purpose |
| --- | --- |
| `marketlab watch` | Loop: quotes, news headlines, research alerts |
| `marketlab once` | Single snapshot of the watchlist |
| `marketlab report` | Stats + trend extraction (SMA stack, log-price slope) |
| `marketlab backtest` | Vectorized strategy backtest (no orders) |
| `marketlab regimes` | Slice a backtest by **any** labeled calendar |

Built-in strategies (extensible): `buy_hold`, `sma_crossover`, `momentum`.

Price providers (pluggable, read-only): **yfinance** (default) and **csv**.

---

## Windows install

1. Install [Python 3.11+](https://www.python.org/downloads/) and tick **Add python.exe to PATH**.
2. Open **Command Prompt** or **PowerShell** in this folder.

```bat
py -3 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
copy config.example.yaml marketlab.yaml
```

Check the CLI:

```bat
marketlab --help
python -m marketlab --help
```

Run tests:

```bat
pytest
```

If `marketlab` is not found after install, use `python -m marketlab` (same commands).

### Optional: stay offline

Use local OHLCV files instead of Yahoo:

```bat
mkdir data\prices
REM Save files named SPY.csv, AAPL.csv, ... with a date column and open,high,low,close,volume
```

In `marketlab.yaml`:

```yaml
provider: csv
csv_data_dir: ./data/prices
```

---

## Quick start

```bat
marketlab once
marketlab report --out report.md
marketlab backtest --symbol SPY --strategy sma_crossover --fast 20 --slow 50
marketlab regimes --symbol SPY --strategy buy_hold --fetcher nber --offline
marketlab regimes --list-calendars
marketlab regimes --list-fetchers
```

`watch` refreshes every 60 seconds (`--interval 30` to change). Ctrl+C stops it. Alerts are console messages only; they never submit orders.

---

## Regime / labeled-period framework

The engine is **generic**. You pass a calendar of `{start, end, label}` windows. The slicer tags each bar with one or more labels. `compare_by_regime(strategy, calendar, prices)` reports, **per label**:

- total return
- max drawdown
- Sharpe-ish (`mean/std * sqrt(252)`, rf = 0)
- win rate (share of in-market days with positive strategy return)
- time in market
- bar count and how many disjoint windows were pooled

Non-contiguous windows that share a label are pooled in time order. Overlapping windows assign the bar to **every** matching label.

**US presidency (Republican vs Democrat) is a demo calendar only** — one sample of the file format, not the product. Compare recessions, VIX regimes, election years, or a YAML file you wrote this afternoon.

### API

```python
from marketlab.regimes import RegimeCalendar, RegimeSlicer, compare_by_regime
from marketlab.strategies import BuyAndHold

calendar = RegimeCalendar.from_file("calendars/my_regimes.yaml")
slicer = RegimeSlicer(calendar, group_by="label")  # or "category" / "metadata.region"
comparison = compare_by_regime(BuyAndHold(), calendar, prices, slicer=slicer)
print(comparison.render())
```

`group_by` selects the slice key: `label`, `category`, or `metadata.<field>`.

### Add a custom calendar file

Create `calendars\my_regimes.yaml` (CSV and JSON work too):

```yaml
name: my_regimes
description: Whatever you want to study
source: me
periods:
  - start: 2018-01-01
    end: 2019-12-31
    label: phase_a
    category: optional_group
    metadata:
      region: US
  - start: 2020-01-01
    end: null          # ongoing / still open
    label: phase_b
```

CSV equivalent:

```text
start,end,label,category
2018-01-01,2019-12-31,phase_a,optional_group
2020-01-01,,phase_b,optional_group
```

Empty / `null` / `ongoing` in `end` means the period is still open.

Then:

```bat
mkdir calendars
REM save my_regimes.yaml in that folder
marketlab regimes --calendar my_regimes --symbol SPY --strategy buy_hold
marketlab regimes --calendar C:\research\calendars\my_regimes.yaml --group-by category
```

Bundled samples (not special-cased in the engine):

| Name | What the labels are |
| --- | --- |
| `us_presidents` | **DEMO** — party (`label`) and president (`category`) |
| `nber_recessions` | `recession` / `expansion` |
| `example_custom` | toy `phase_a` / `phase_b` |

### Add / use a fetcher (online or derived)

Fetchers turn a public series or a rule into a `RegimeCalendar`. Built-in:

| `--fetcher` | Source |
| --- | --- |
| `nber` | FRED `USREC` (monthly 0/1); bundled NBER dates if offline / `--offline` |
| `vix` | High/low vol from `^VIX` via the price provider (hysteresis 25 / 15) |
| `election_years` | Computed US presidential election year vs other years |
| `presidents` | Loads the **demo** bundled party calendar |

```bat
marketlab regimes --fetcher nber --symbol SPY --strategy buy_hold
marketlab regimes --fetcher vix --symbol SPY --strategy sma_crossover
marketlab regimes --fetcher election_years --group-by label --offline
```

Register your own in Python:

```python
from datetime import date
from marketlab.regimes.calendar import RegimeCalendar, RegimePeriod
from marketlab.regimes.fetchers import RegimeFetcher, register_fetcher

@register_fetcher("fed_example")
class FedExampleFetcher(RegimeFetcher):
    description = "Illustration — replace with a real public series"

    def fetch(self, *, allow_network: bool = True) -> RegimeCalendar:
        periods = [
            RegimePeriod(date(2015, 12, 16), date(2018, 12, 19), "hiking"),
            RegimePeriod(date(2018, 12, 20), date(2019, 7, 30), "pause"),
        ]
        return RegimeCalendar(name="fed_example", periods=periods, source="example")
```

Point the CLI at it:

```bat
marketlab regimes --fetcher my_package.regimes:FedExampleFetcher --symbol SPY
```

(`module:Class` or a name already passed to `register_fetcher`.)

---

## Config

`config.example.yaml` documents the keys. Copy it to `marketlab.yaml` in the working directory, or pass `-c path\to\config.yaml`.

`--watchlist SPY,QQQ,AAPL` overrides the file for one invocation.

---

## Extending strategies

```python
from marketlab.strategies import Strategy, register_strategy
import pandas as pd

class MyRule(Strategy):
    name = "my_rule"

    def generate_signals(self, prices: pd.DataFrame) -> pd.Series:
        # 1 = long, 0 = flat. These are research positions, not orders.
        return (prices["close"].pct_change() > 0).astype(float)

register_strategy("my_rule", lambda **_: MyRule())
```

The backtester lags signals by one bar (no same-close look-ahead) and never routes them anywhere.

---

## Disclaimer (read it)

Descriptive research only. Regime statistics summarize labeled historical windows; they are not evidence that a label caused returns. **Correlation is not causation.** This program never places trades and is not trading advice, an offer to transact, or a recommendation to buy or sell any security.
