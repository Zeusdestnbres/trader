from pathlib import Path

# Concatenated API-style tokens only. Prose that says we do *not* integrate
# Trading 212 is allowed (see disclaimer.py).
FORBIDDEN = (
    "trading212",
    "place_order",
    "submit_order",
    "create_order",
    "send_order",
)


def test_source_has_no_broker_or_order_api() -> None:
    root = Path(__file__).resolve().parents[1] / "src"
    hits: list[str] = []
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        for token in FORBIDDEN:
            if token in text:
                hits.append(f"{path}: {token}")
    assert hits == []
