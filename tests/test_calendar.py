from datetime import date
from pathlib import Path

from marketlab.regimes.calendar import RegimeCalendar, RegimePeriod, load_calendar


def test_load_yaml_csv_json(sample_calendar_dir: Path) -> None:
    yaml_cal = RegimeCalendar.from_file(sample_calendar_dir / "toy.yaml")
    csv_cal = RegimeCalendar.from_file(sample_calendar_dir / "toy.csv")
    json_cal = RegimeCalendar.from_file(sample_calendar_dir / "toy.json")
    assert yaml_cal.unique_labels() == ["first_half", "second_half"]
    assert csv_cal.unique_labels() == yaml_cal.unique_labels()
    assert json_cal.name == "toy_json"
    assert yaml_cal.labels_at(date(2018, 3, 1)) == ["first_half"]
    assert yaml_cal.labels_at(date(2018, 8, 1)) == ["second_half"]
    assert yaml_cal.labels_at(date(2017, 1, 1)) == []


def test_ongoing_end(tmp_path: Path) -> None:
    path = tmp_path / "open.yaml"
    path.write_text(
        """
name: open_ended
periods:
  - start: 2025-01-20
    end: null
    label: current
""",
        encoding="utf-8",
    )
    cal = RegimeCalendar.from_file(path)
    assert cal.periods[0].end is None
    assert cal.periods[0].contains(date(2026, 9, 17))


def test_bundled_presidents_is_demo_not_product() -> None:
    cal = load_calendar("us_presidents")
    assert cal.name == "us_presidents"
    labels = set(cal.unique_labels())
    assert "Republican" in labels and "Democrat" in labels
    names = cal.unique_labels("category")
    assert "Joe Biden" in names
    assert cal.labels_at(date(2020, 6, 1)) == ["Republican"]
    assert cal.labels_at(date(2022, 6, 1)) == ["Democrat"]


def test_bundled_nber_and_example() -> None:
    nber = load_calendar("nber_recessions")
    assert "recession" in nber.unique_labels()
    assert "expansion" in nber.unique_labels()
    assert nber.labels_at(date(2008, 10, 1)) == ["recession"]
    assert nber.labels_at(date(2015, 6, 1)) == ["expansion"]
    custom = load_calendar("example_custom")
    assert custom.labels_at(date(2018, 5, 1)) == ["phase_a"]


def test_user_dir_overrides_by_path(sample_calendar_dir: Path) -> None:
    cal = load_calendar(sample_calendar_dir / "toy.yaml")
    assert cal.name == "toy"


def test_overlap_multiple_labels() -> None:
    cal = RegimeCalendar(
        name="overlap",
        periods=[
            RegimePeriod(date(2020, 1, 1), date(2020, 12, 31), "alpha"),
            RegimePeriod(date(2020, 6, 1), date(2020, 8, 31), "beta"),
        ],
    )
    labels = cal.labels_at(date(2020, 7, 4))
    assert labels == ["alpha", "beta"]
