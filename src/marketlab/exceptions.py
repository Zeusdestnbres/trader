class MarketLabError(Exception):
    """Base error for the research toolkit."""


class ConfigError(MarketLabError):
    pass


class ProviderError(MarketLabError):
    pass


class CalendarError(MarketLabError):
    pass


class StrategyError(MarketLabError):
    pass


class FetcherError(MarketLabError):
    pass
