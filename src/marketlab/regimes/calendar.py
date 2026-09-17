from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import date, datetime
from importlib import resources
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import yaml

from marketlab.exceptions import CalendarError

ONGOING_SENTINELS = {"", "null", "none", "ongoing", "open", "present"}


@dataclass(frozen=True)
class RegimePeriod:
    """A labeled time window. ``end`` is None for an open-ended (ongoing) period."""

    start: date
    end: date | None
    label: str
    category: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def contains(self, day: date) -> bool:
        if day < self.start:
            return False
        if self.end is None:
            return True
        return day <= self.end

    def group_key(self, group_by: str = "label") -> str:
        gb = (group_by or "label").strip()
        if gb == "label":
            return self.label
        if gb == "category":
            return self.category or self.label
        if gb.startswith("metadata."):
            key = gb.split(".", 1)[1]
            value = self.metadata.get(key)
            return str(value) if value not in (None, "") else self.label
        # treat unknown group_by as metadata key, then label
        if gb in self.metadata:
            return str(self.metadata[gb])
        return self.label


@dataclass
class RegimeCalendar:
    """Named collection of labeled periods. Format-agnostic research input."""

    name: str
    periods: list[RegimePeriod]
    source: str = ""
    description: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def unique_labels(self, group_by: str = "label") -> list[str]:
        seen: list[str] = []
        for period in self.periods:
            key = period.group_key(group_by)
            if key not in seen:
                seen.append(key)
        return seen

    def covering(self, day: date) -> list[RegimePeriod]:
        return [p for p in self.periods if p.contains(day)]

    def labels_at(self, day: date, group_by: str = "label") -> list[str]:
        keys: list[str] = []
        for period in self.covering(day):
            key = period.group_key(group_by)
            if key not in keys:
                keys.append(key)
        return keys

    @classmethod
    def from_file(cls, path: str | Path) -> RegimeCalendar:
        p = Path(path)
        if not p.exists():
            raise CalendarError(f"calendar file not found: {p}")
        suffix = p.suffix.lower()
        if suffix in {".yaml", ".yml"}:
            return cls.from_yaml(p)
        if suffix == ".json":
            return cls.from_json(p)
        if suffix == ".csv":
            return cls.from_csv(p)
        raise CalendarError(f"unsupported calendar format {suffix} (use yaml/json/csv)")

    @classmethod
    def from_yaml(cls, path: str | Path) -> RegimeCalendar:
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        return cls.from_mapping(raw, default_name=Path(path).stem, source=str(path))

    @classmethod
    def from_json(cls, path: str | Path) -> RegimeCalendar:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_mapping(raw, default_name=Path(path).stem, source=str(path))

    @classmethod
    def from_csv(cls, path: str | Path) -> RegimeCalendar:
        with Path(path).open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
        periods = [_period_from_mapping(row) for row in rows]
        if not periods:
            raise CalendarError(f"CSV calendar has no periods: {path}")
        return cls(name=Path(path).stem, periods=periods, source=str(path), description="CSV calendar")

    @classmethod
    def from_mapping(
        cls,
        raw: Any,
        *,
        default_name: str = "calendar",
        source: str = "",
    ) -> RegimeCalendar:
        if not isinstance(raw, dict):
            raise CalendarError("calendar document must be a mapping with a 'periods' list")
        rows = raw.get("periods")
        if not isinstance(rows, list) or not rows:
            raise CalendarError("calendar must include a non-empty 'periods' list")
        periods = [_period_from_mapping(row) for row in rows]
        extra = {k: v for k, v in raw.items() if k not in {"name", "periods", "source", "description"}}
        return cls(
            name=str(raw.get("name") or default_name),
            periods=periods,
            source=str(raw.get("source") or source),
            description=str(raw.get("description") or ""),
            extra=extra,
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "source": self.source,
            "description": self.description,
            "periods": [
                {
                    "start": p.start.isoformat(),
                    "end": None if p.end is None else p.end.isoformat(),
                    "label": p.label,
                    "category": p.category,
                    "metadata": dict(p.metadata),
                }
                for p in self.periods
            ],
        }


def _period_from_mapping(row: Mapping[str, Any]) -> RegimePeriod:
    if not isinstance(row, Mapping):
        raise CalendarError(f"period must be a mapping, got {type(row)}")
    start = parse_iso_date(row.get("start") or row.get("begin") or row.get("from"))
    if start is None:
        raise CalendarError(f"period missing start date: {row}")
    end = parse_iso_date(row.get("end") or row.get("to") or row.get("until"), allow_ongoing=True)
    label = row.get("label") or row.get("name") or row.get("regime")
    if not label:
        raise CalendarError(f"period missing label: {row}")
    category = row.get("category")
    metadata = row.get("metadata") or {}
    if not isinstance(metadata, Mapping):
        raise CalendarError("metadata must be a mapping")
    # Promote leftover scalar columns (CSV) into metadata
    skip = {
        "start",
        "end",
        "begin",
        "from",
        "to",
        "until",
        "label",
        "name",
        "regime",
        "category",
        "metadata",
    }
    extra = {str(k): str(v) for k, v in row.items() if k not in skip and v not in (None, "")}
    merged = {**{str(k): str(v) for k, v in metadata.items()}, **extra}
    return RegimePeriod(
        start=start,
        end=end,
        label=str(label),
        category=None if category in (None, "") else str(category),
        metadata=merged,
    )


def parse_iso_date(value: Any, *, allow_ongoing: bool = False) -> date | None:
    if value is None:
        return None if allow_ongoing else None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if allow_ongoing and text.lower() in ONGOING_SENTINELS:
        return None
    if not text:
        return None if allow_ongoing else None
    try:
        return date.fromisoformat(text[:10])
    except ValueError as exc:
        raise CalendarError(f"invalid date {value!r}") from exc


def bundled_calendar_dir() -> Path:
    traversable = resources.files("marketlab.data.calendars")
    return Path(str(traversable))


def iter_bundled_calendar_files() -> Iterable[Path]:
    root = resources.files("marketlab.data.calendars")
    for item in root.iterdir():
        name = getattr(item, "name", "")
        if name.endswith((".yaml", ".yml", ".json", ".csv")):
            yield Path(str(item))


def load_calendar(
    ref: str | Path,
    *,
    extra_dirs: Sequence[str | Path] | None = None,
) -> RegimeCalendar:
    """Load by filesystem path, or by bundled/extra-dir stem name (e.g. ``us_presidents``)."""
    path = Path(ref)
    if path.exists() and path.is_file():
        return RegimeCalendar.from_file(path)

    stem = str(ref)
    search: list[Path] = []
    for extra in extra_dirs or []:
        search.append(Path(extra))
    search.append(Path("calendars"))
    try:
        search.append(bundled_calendar_dir())
    except Exception:
        pass

    matches: list[Path] = []
    for folder in search:
        if not folder.exists():
            # importlib.resources may yield a virtual path; try as file via resources
            continue
        for ext in (".yaml", ".yml", ".json", ".csv"):
            candidate = folder / f"{stem}{ext}"
            if candidate.exists():
                matches.append(candidate)
    if matches:
        return RegimeCalendar.from_file(matches[0])

    # Bundled via importlib even if Path.exists() is false on some zip installs
    root = resources.files("marketlab.data.calendars")
    for ext in (".yaml", ".yml", ".json", ".csv"):
        item = root.joinpath(f"{stem}{ext}")
        if item.is_file():
            text = item.read_text(encoding="utf-8")
            tmp = {
                ".yaml": RegimeCalendar.from_mapping,
                ".yml": RegimeCalendar.from_mapping,
            }
            if ext in {".yaml", ".yml"}:
                return RegimeCalendar.from_mapping(
                    yaml.safe_load(text), default_name=stem, source=f"bundled:{stem}{ext}"
                )
            if ext == ".json":
                return RegimeCalendar.from_mapping(
                    json.loads(text), default_name=stem, source=f"bundled:{stem}{ext}"
                )
    raise CalendarError(
        f"calendar {ref!r} not found. Drop a YAML/CSV/JSON file in ./calendars "
        f"or pass a path. Bundled samples: us_presidents, nber_recessions, example_custom."
    )
