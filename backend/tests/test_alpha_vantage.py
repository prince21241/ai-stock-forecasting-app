from decimal import Decimal

import httpx
import pytest

from app.core.exceptions import (
    AlphaVantageMalformedResponseError,
    AlphaVantageRateLimitError,
    AlphaVantageTimeoutError,
    InvalidSymbolError,
)
from app.services.alpha_vantage import AlphaVantageClient
from app.utils.validation import normalize_symbol


def test_valid_symbol_normalization() -> None:
    assert normalize_symbol(" brk.b ") == "BRK.B"
    assert normalize_symbol("rds-a") == "RDS-A"


@pytest.mark.parametrize("symbol", ["", "A APL", "../AAPL", "<script>", "A" * 16, "AAPL/"])
def test_invalid_symbol_rejection(symbol: str) -> None:
    with pytest.raises(InvalidSymbolError):
        normalize_symbol(symbol)


def test_successful_alpha_vantage_parsing(daily_payload: dict) -> None:
    records = AlphaVantageClient.parse_daily_response("AAPL", daily_payload)
    assert len(records) == 2
    assert records[0].trading_date.isoformat() == "2024-01-02"
    assert records[1].close_price == Decimal("103.2500")


def test_alpha_vantage_invalid_symbol_response() -> None:
    with pytest.raises(InvalidSymbolError):
        AlphaVantageClient.parse_daily_response("NOPE", {"Error Message": "Invalid API call"})


@pytest.mark.parametrize("field", ["Note", "Information"])
def test_alpha_vantage_rate_limit_response(field: str) -> None:
    with pytest.raises(AlphaVantageRateLimitError):
        AlphaVantageClient.parse_daily_response("AAPL", {field: "frequency limit"})


@pytest.mark.parametrize(
    "payload", [{}, {"Time Series (Daily)": {}}, {"Time Series (Daily)": {"bad": {}}}]
)
def test_alpha_vantage_malformed_response(payload: dict) -> None:
    with pytest.raises(AlphaVantageMalformedResponseError):
        AlphaVantageClient.parse_daily_response("AAPL", payload)


@pytest.mark.asyncio
async def test_alpha_vantage_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    class TimeoutClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            return None

        async def get(self, *_args, **_kwargs):
            raise httpx.ReadTimeout("timed out")

    monkeypatch.setattr(httpx, "AsyncClient", lambda **_kwargs: TimeoutClient())
    client = AlphaVantageClient("test-key", "https://example.test")
    with pytest.raises(AlphaVantageTimeoutError):
        await client.fetch_daily("AAPL")
