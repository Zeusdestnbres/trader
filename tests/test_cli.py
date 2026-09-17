from marketlab.cli import _build_parser, main
from tests.conftest import make_prices, write_ohlcv_csv


def test_help_lists_research_commands() -> None:
    text = _build_parser().format_help()
    for cmd in ("watch", "once", "report", "backtest", "regimes"):
        assert cmd in text
    assert "never" in text.lower() or "research" in text.lower()


def test_list_fetchers_and_calendars(capsys) -> None:
    assert main(["regimes", "--list-fetchers"]) == 0
    out = capsys.readouterr().out
    assert "nber" in out
    assert "vix" in out
    assert "DEMO" in out
    assert main(["regimes", "--list-calendars"]) == 0
    cal_out = capsys.readouterr().out
    assert "us_presidents" in cal_out
    assert "nber_recessions" in cal_out
    assert "DEMO" in cal_out


def test_backtest_and_regimes_offline_csv(tmp_path, capsys) -> None:
    prices = make_prices(start="2018-01-02", periods=260, seed=7)
    write_ohlcv_csv(tmp_path / "SPY.csv", prices)
    cfg = tmp_path / "marketlab.yaml"
    cfg.write_text(
        f"""
watchlist: [SPY]
provider: csv
csv_data_dir: {tmp_path.as_posix()}
backtest:
  strategy: buy_hold
  start: "2018-01-01"
""",
        encoding="utf-8",
    )
    assert main(["-c", str(cfg), "backtest", "--symbol", "SPY", "--strategy", "buy_hold"]) == 0
    bt = capsys.readouterr().out
    assert "buy_hold" in bt
    assert "return:" in bt

    cal = tmp_path / "phases.yaml"
    cal.write_text(
        """
name: phases
periods:
  - start: 2018-01-01
    end: 2018-12-31
    label: y2018
  - start: 2019-01-01
    end: 2019-12-31
    label: y2019
""",
        encoding="utf-8",
    )
    assert (
        main(
            [
                "-c",
                str(cfg),
                "regimes",
                "--symbol",
                "SPY",
                "--strategy",
                "buy_hold",
                "--calendar",
                str(cal),
                "--group-by",
                "label",
            ]
        )
        == 0
    )
    rg = capsys.readouterr().out
    assert "y2018" in rg
    assert "y2019" in rg
    assert "causation" in rg.lower() or "Descriptive" in rg


def test_once_csv(tmp_path, capsys) -> None:
    prices = make_prices(periods=80, seed=4)
    write_ohlcv_csv(tmp_path / "AAPL.csv", prices)
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text(
        f"""
watchlist: [AAPL]
provider: csv
csv_data_dir: {tmp_path.as_posix()}
news:
  enabled: false
alerts:
  pct_change: 50
  sma_cross: false
""",
        encoding="utf-8",
    )
    assert main(["-c", str(cfg), "once"]) == 0
    out = capsys.readouterr().out
    assert "AAPL" in out


def test_report_writes_file(tmp_path) -> None:
    prices = make_prices(periods=80, seed=5)
    write_ohlcv_csv(tmp_path / "MSFT.csv", prices)
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text(
        f"""
watchlist: [MSFT]
provider: csv
csv_data_dir: {tmp_path.as_posix()}
news:
  enabled: false
""",
        encoding="utf-8",
    )
    out = tmp_path / "report.md"
    assert main(["-c", str(cfg), "report", "--out", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert "MSFT" in text
    assert "Trend" in text or "trend" in text
