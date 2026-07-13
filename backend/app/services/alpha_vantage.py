from datetime import date
from decimal import Decimal, InvalidOperation

import httpx

from app.core.exceptions import (
    AlphaVantageMalformedResponseError,
    AlphaVantageNetworkError,
    AlphaVantageRateLimitError,
    AlphaVantageTimeoutError,
    InvalidSymbolError,
    MissingAPIKeyError,
)
from app.schemas.stock import StockPriceCreate
from app.utils.validation import normalize_symbol


class AlphaVantageClient:
    def __init__(self, api_key: str, base_url: str, timeout: float = 15.0) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout

    async def fetch_daily(self, raw_symbol: str) -> list[StockPriceCreate]:
        symbol = normalize_symbol(raw_symbol)
        if not self.api_key or self.api_key == "replace_with_your_key":
            raise MissingAPIKeyError("Alpha Vantage API key is not configured.")
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    self.base_url,
                    params={
                        "function": "TIME_SERIES_DAILY",
                        "symbol": symbol,
                        "apikey": self.api_key,
                    },
                )
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise AlphaVantageTimeoutError("Alpha Vantage request timed out.") from exc
        except httpx.HTTPError as exc:
            raise AlphaVantageNetworkError("Alpha Vantage request failed.") from exc
        try:
            payload = response.json()
        except ValueError as exc:
            raise AlphaVantageMalformedResponseError(
                "Alpha Vantage returned invalid JSON."
            ) from exc
        return self.parse_daily_response(symbol, payload)

    @staticmethod
    def parse_daily_response(symbol: str, payload: object) -> list[StockPriceCreate]:
        if not isinstance(payload, dict):
            raise AlphaVantageMalformedResponseError("Alpha Vantage response is malformed.")
        if "Error Message" in payload:
            raise InvalidSymbolError("Alpha Vantage did not recognize this stock symbol.")
        if "Note" in payload or "Information" in payload:
            raise AlphaVantageRateLimitError("Alpha Vantage rate limit has been reached.")
        series = payload.get("Time Series (Daily)")
        if not isinstance(series, dict) or not series:
            raise AlphaVantageMalformedResponseError(
                "Daily time series is missing from the response."
            )
        records: list[StockPriceCreate] = []
        try:
            for raw_date, values in series.items():
                if not isinstance(values, dict):
                    raise ValueError
                records.append(
                    StockPriceCreate(
                        symbol=symbol,
                        trading_date=date.fromisoformat(raw_date),
                        open_price=Decimal(values["1. open"]),
                        high_price=Decimal(values["2. high"]),
                        low_price=Decimal(values["3. low"]),
                        close_price=Decimal(values["4. close"]),
                        volume=int(values["5. volume"]),
                    )
                )
        except (KeyError, TypeError, ValueError, InvalidOperation) as exc:
            raise AlphaVantageMalformedResponseError(
                "Daily time series contains invalid values."
            ) from exc
        return sorted(records, key=lambda item: item.trading_date)
