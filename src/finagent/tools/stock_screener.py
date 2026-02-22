"""stock_screener tool — premium stock screening with license gating."""

from __future__ import annotations

import json
from typing import Any

from finagent.license import require_license
from finagent.services.screener import ScreenerService

_service = ScreenerService()


def stock_screener(
    filters: dict[str, Any],
    sort_by: str | None = None,
    limit: int = 20,
) -> str:
    """Screen stocks by financial criteria.

    PREMIUM FEATURE — requires a FinAgent license key.

    Args:
        filters: Dict of filter criteria.  Supported keys:
            sector (str), market_cap_min/max (float),
            pe_ratio_min/max (float), revenue_growth_min (float),
            dividend_yield_min (float).
        sort_by: Optional field name to sort results by (descending).
        limit: Maximum number of results to return (default 20).

    Returns:
        JSON string with a list of matching stocks or an error object.
    """
    gate = require_license("stock_screener")
    if gate is not None:
        return gate

    try:
        results = _service.screen(filters=filters, sort_by=sort_by, limit=limit)
    except Exception as exc:
        return json.dumps({"error": "service_error", "message": str(exc)})

    return json.dumps(results, default=str)
