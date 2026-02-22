"""sec_filings tool — premium SEC EDGAR filing access with license gating."""

from __future__ import annotations

import json

from finagent.license import require_license
from finagent.services.sec_edgar import SECEdgarService

_service = SECEdgarService()


def sec_filings(
    ticker: str,
    filing_type: str = "10-K",
    section: str | None = None,
    date_range: str | None = None,
) -> str:
    """Retrieve SEC filing data for a company.

    PREMIUM FEATURE — requires a FinAgent license key.

    Args:
        ticker: Stock ticker symbol (e.g. "AAPL", "MSFT").
        filing_type: SEC form type — "10-K", "10-Q", "8-K", or "DEF-14A".
        section: Section to extract from a 10-K filing. One of:
            business_overview, risk_factors, item_7, item_7a,
            financial_statements.  Omit to get filing metadata and
            a list of available sections.
        date_range: Optional date filter (reserved for future use).

    Returns:
        JSON string with filing data or an error object.
    """
    gate = require_license("sec_filings")
    if gate is not None:
        return gate

    try:
        result = _service.get_filing_section(
            ticker=ticker,
            filing_type=filing_type,
            section=section,
            date_range=date_range,
        )
    except Exception as exc:
        return json.dumps({"error": "service_error", "message": str(exc)})

    return json.dumps(result, default=str)
