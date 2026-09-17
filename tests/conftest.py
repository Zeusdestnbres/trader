from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest


def make_prices(
    *,
    start: str = "2018-01-02",
    periods: int = 400,
    seed: int = 0,
    drift: float = 0.0004,
    sigma: float = 0.01,
    start_price: float = 100.0,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range(start, periods=periods)
    rets = rng.normal(drift, sigma, size=len(idx))
    close = start_price * np.cumprod(1.0 + rets)
    return pd.DataFrame(
        {
            "open": close,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": 1_000_000.0,
        },
        index=idx,
    )


def write_ohlcv_csv(path: Path, frame: pd.DataFrame) -> Path:
    out = frame.copy()
    out.index.name = "date"
    out.to_csv(path)
    return path


@pytest.fixture
def prices() -> pd.DataFrame:
    return make_prices()


@pytest.fixture
def sample_calendar_dir(tmp_path: Path) -> Path:
    yaml_text = """
name: toy
description: unit-test calendar
periods:
  - start: 2018-01-01
    end: 2018-06-30
    label: first_half
    category: toy
  - start: 2018-07-01
    end: 2018-12-31
    label: second_half
    category: toy
"""
    (tmp_path / "toy.yaml").write_text(yaml_text, encoding="utf-8")
    csv_text = "start,end,label,category\n2018-01-01,2018-06-30,first_half,toy\n2018-07-01,2018-12-31,second_half,toy\n"
    (tmp_path / "toy.csv").write_text(csv_text, encoding="utf-8")
    json_text = """
{
  "name": "toy_json",
  "periods": [
    {"start": "2018-01-01", "end": "2018-06-30", "label": "first_half", "category": "toy"},
    {"start": "2018-07-01", "end": "2018-12-31", "label": "second_half", "category": "toy"}
  ]
}
"""
    (tmp_path / "toy.json").write_text(json_text, encoding="utf-8")
    return tmp_path
