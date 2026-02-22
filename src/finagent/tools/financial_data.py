"""Compound financial_data tool that dispatches to MarketDataService methods."""

from __future__ import annotations

import json
from typing import Any

from finagent.services.market_data import MarketDataService

_service = MarketDataService()

VALID_DATA_TYPES = (
    "quote",
    "income_statement",
    "balance_sheet",
    "cash_flow",
    "analyst_estimates",
    "insider_trades",
    "key_ratios",
)

_DISPATCH: dict[str, str] = {
    "quote": "get_quote",
    "income_statement": "get_income_statement",
    "balance_sheet": "get_balance_sheet",
    "cash_flow": "get_cash_flow",
    "analyst_estimates": "get_analyst_estimates",
    "insider_trades": "get_insider_trades",
    "key_ratios": "get_key_ratios",
}


def financial_data(
    ticker: str,
    data_type: str,
    period: str = "annual",
    limit: int = 4,
) -> str:
    """Retrieve financial data for a stock ticker.

    Args:
        ticker: Stock ticker symbol (e.g. "AAPL", "MSFT").
        data_type: One of: quote, income_statement, balance_sheet,
            cash_flow, analyst_estimates, insider_trades, key_ratios.
        period: Reporting period — "annual" or "quarterly" (default "annual").
        limit: Maximum number of periods to return (default 4).

    Returns:
        JSON string with the requested data or an error object.
    """
    if data_type not in VALID_DATA_TYPES:
        return json.dumps(
            {
                "error": "invalid_data_type",
                "message": (
                    f"Invalid data_type '{data_type}'. "
                    f"Must be one of: {', '.join(VALID_DATA_TYPES)}"
                ),
            }
        )

    method_name = _DISPATCH[data_type]
    method = getattr(_service, method_name)

    try:
        result: Any = method(ticker)
    except Exception as exc:
        return json.dumps({"error": "service_error", "message": str(exc)})

    # Apply limit to list results (financial statements)
    if isinstance(result, list):
        result = result[:limit]

    return json.dumps(result, default=str)
