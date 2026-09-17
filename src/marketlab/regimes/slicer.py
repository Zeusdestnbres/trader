from __future__ import annotations

from datetime import date

import pandas as pd

from marketlab.regimes.calendar import RegimeCalendar

UNLABELED = "_unlabeled"


def as_date(ts) -> date:
    t = pd.Timestamp(ts)
    if t.tzinfo is not None:
        t = t.tz_convert("UTC").tz_localize(None)
    return t.date()


class RegimeSlicer:
    """Tag each bar/return with one or more calendar labels."""

    def __init__(self, calendar: RegimeCalendar, *, group_by: str = "label") -> None:
        self.calendar = calendar
        self.group_by = group_by or "label"

    def labels_for(self, ts) -> list[str]:
        return self.calendar.labels_at(as_date(ts), group_by=self.group_by)

    def tag_index(self, index: pd.Index) -> pd.Series:
        """Primary label per timestamp (first covering period). Unlabeled → empty string."""
        values = []
        for ts in index:
            labels = self.labels_for(ts)
            values.append(labels[0] if labels else "")
        return pd.Series(values, index=index, name="regime")

    def tags_index(self, index: pd.Index) -> pd.Series:
        """All labels per timestamp (list). Overlapping periods keep every match."""
        return pd.Series([self.labels_for(ts) for ts in index], index=index, name="regimes")

    def mask(self, index: pd.Index, label: str) -> pd.Series:
        tags = self.tags_index(index)
        return tags.map(lambda xs: label in xs)

    def labeled_frame(self, returns: pd.Series) -> pd.DataFrame:
        primary = self.tag_index(returns.index)
        multi = self.tags_index(returns.index)
        return pd.DataFrame(
            {
                "return": returns.astype(float),
                "regime": primary.replace("", UNLABELED),
                "regimes": multi,
            }
        )
