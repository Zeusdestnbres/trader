from marketlab.providers.base import PriceProvider
from marketlab.providers.csv_provider import CsvPriceProvider
from marketlab.providers.yfinance_provider import YFinanceProvider

__all__ = ["PriceProvider", "CsvPriceProvider", "YFinanceProvider", "build_provider"]


def build_provider(name: str, *, csv_data_dir: str | None = None) -> PriceProvider:
    key = name.lower().strip()
    if key in {"yfinance", "yahoo"}:
        return YFinanceProvider()
    if key == "csv":
        if not csv_data_dir:
            raise ValueError("csv provider requires csv_data_dir")
        return CsvPriceProvider(csv_data_dir)
    raise ValueError(
        f"unknown price provider {name!r}. Built-in: yfinance, csv. "
        "This toolkit never places trades and has no broker providers."
    )
