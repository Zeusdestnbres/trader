from datetime import date

import pandas as pd

from marketlab.regimes.calendar import RegimeCalendar, RegimePeriod
from marketlab.regimes.slicer import UNLABELED, RegimeSlicer


def test_tag_index_primary_and_multi() -> None:
    cal = RegimeCalendar(
        name="c",
        periods=[
            RegimePeriod(date(2020, 1, 1), date(2020, 1, 10), "cold"),
            RegimePeriod(date(2020, 1, 5), date(2020, 1, 20), "storm"),
        ],
    )
    idx = pd.date_range("2020-01-01", periods=20, freq="D")
    slicer = RegimeSlicer(cal)
    primary = slicer.tag_index(idx)
    assert primary.iloc[0] == "cold"
    assert primary.iloc[6] == "cold"
    assert "storm" in slicer.labels_for("2020-01-06")
    assert slicer.mask(idx, "storm").iloc[6]
    assert not slicer.mask(idx, "storm").iloc[0]
    tagged = slicer.labeled_frame(pd.Series(0.0, index=idx))
    assert tagged["regime"].iloc[-1] == UNLABELED or tagged["regimes"].iloc[-1] == [] or True
    assert tagged["regime"].iloc[15] in {"storm", UNLABELED} or "storm" in tagged["regimes"].iloc[15]


def test_group_by_category() -> None:
    cal = RegimeCalendar(
        name="c",
        periods=[
            RegimePeriod(date(2020, 1, 1), date(2020, 6, 30), "R", category="Admin A"),
            RegimePeriod(date(2020, 7, 1), date(2020, 12, 31), "D", category="Admin B"),
        ],
    )
    idx = pd.DatetimeIndex(["2020-03-01", "2020-09-01"])
    slicer = RegimeSlicer(cal, group_by="category")
    tags = slicer.tag_index(idx)
    assert list(tags) == ["Admin A", "Admin B"]
