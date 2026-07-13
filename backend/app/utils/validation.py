import re

from app.core.exceptions import InvalidSymbolError

SYMBOL_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9.-]{0,14}$")


def normalize_symbol(value: str) -> str:
    symbol = value.strip().upper()
    if not symbol or not SYMBOL_PATTERN.fullmatch(symbol):
        raise InvalidSymbolError(
            "Invalid stock symbol. Use 1-15 letters, numbers, periods, or hyphens without spaces."
        )
    if ".." in symbol or "--" in symbol or symbol.endswith((".", "-")):
        raise InvalidSymbolError("Invalid stock symbol format.")
    return symbol
