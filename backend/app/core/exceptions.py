class StockAgentError(Exception):
    """Base domain exception with a safe public message."""


class InvalidSymbolError(StockAgentError):
    pass


class AlphaVantageError(StockAgentError):
    pass


class AlphaVantageRateLimitError(AlphaVantageError):
    pass


class AlphaVantageMalformedResponseError(AlphaVantageError):
    pass


class AlphaVantageTimeoutError(AlphaVantageError):
    pass


class AlphaVantageNetworkError(AlphaVantageError):
    pass


class MissingAPIKeyError(AlphaVantageError):
    pass
