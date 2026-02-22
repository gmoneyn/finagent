"""Stock screener service — screens a curated universe of tickers by financial criteria."""

from __future__ import annotations

import logging
from typing import Any

import yfinance as yf

from finagent.cache import FileCache

logger = logging.getLogger(__name__)

# Cache TTL for individual stock info lookups (seconds)
TTL_STOCK_INFO = 3600  # 1 hour

# Curated universe of ~70 liquid, well-known tickers across sectors
SCREEN_UNIVERSE = [
    # Mega-cap Tech
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "AVGO",
    "ORCL", "CRM", "ADBE", "AMD", "INTC", "CSCO", "IBM",
    # Financials
    "JPM", "BAC", "WFC", "GS", "MS", "C", "BLK", "SCHW", "AXP", "V", "MA",
    # Healthcare
    "JNJ", "UNH", "PFE", "ABBV", "MRK", "LLY", "TMO", "ABT", "BMY", "AMGN",
    # Energy
    "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX",
    # Consumer Discretionary
    "HD", "MCD", "NKE", "SBUX", "TGT", "LOW", "TJX", "BKNG",
    # Consumer Staples
    "PG", "KO", "PEP", "COST", "WMT", "CL", "MDLZ",
    # Industrials
    "CAT", "BA", "HON", "UPS", "GE", "RTX", "LMT", "DE",
    # Utilities & REITs
    "NEE", "DUK", "SO", "AMT", "PLD",
    # Telecom / Communication
    "DIS", "NFLX", "CMCSA", "T", "VZ",
]


class ScreenerService:
    """Screens stocks from a curated universe by financial criteria."""

    def __init__(self, cache: FileCache | None = None, universe: list[str] | None = None):
        self.cache = cache or FileCache()
        self.universe = universe or SCREEN_UNIVERSE

    def _get_stock_info(self, ticker: str) -> dict[str, Any] | None:
        """Get yfinance info for a single ticker, cached for 1 hour.

        Returns a normalised dict with screening-relevant fields,
        or None if the ticker is invalid / data unavailable.
        """
        cache_key = f"screener_info:{ticker}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            t = yf.Ticker(ticker)
            info = t.info
        except Exception:
            logger.warning("Failed to fetch info for %s", ticker)
            return None

        # Validate — yfinance returns stubs for invalid tickers
        if not info or ("currentPrice" not in info and "regularMarketPrice" not in info):
            return None

        result: dict[str, Any] = {
            "ticker": ticker,
            "name": info.get("shortName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "dividend_yield": info.get("dividendYield"),
            "revenue_growth": info.get("revenueGrowth"),
            "profit_margin": info.get("profitMargins"),
            "return_on_equity": info.get("returnOnEquity"),
            "beta": info.get("beta"),
            "52_week_high": info.get("fiftyTwoWeekHigh"),
            "52_week_low": info.get("fiftyTwoWeekLow"),
        }

        self.cache.set(cache_key, result, ttl_seconds=TTL_STOCK_INFO)
        return result

    @staticmethod
    def _matches_filters(info: dict[str, Any], filters: dict[str, Any]) -> bool:
        """Check whether a stock info dict satisfies all filter criteria."""
        for key, value in filters.items():
            if key == "sector":
                if info.get("sector") is None:
                    return False
                if value.lower() not in info["sector"].lower():
                    return False

            elif key == "market_cap_min":
                mc = info.get("market_cap")
                if mc is None or mc < value:
                    return False

            elif key == "market_cap_max":
                mc = info.get("market_cap")
                if mc is None or mc > value:
                    return False

            elif key == "pe_ratio_min":
                pe = info.get("pe_ratio")
                if pe is None or pe < value:
                    return False

            elif key == "pe_ratio_max":
                pe = info.get("pe_ratio")
                if pe is None or pe > value:
                    return False

            elif key == "revenue_growth_min":
                rg = info.get("revenue_growth")
                if rg is None or rg < value:
                    return False

            elif key == "dividend_yield_min":
                dy = info.get("dividend_yield")
                if dy is None or dy < value:
                    return False

        return True

    def screen(
        self,
        filters: dict[str, Any],
        sort_by: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Screen the stock universe by the given filters.

        Args:
            filters: Dict of filter criteria.  Supported keys:
                sector (str), market_cap_min/max (float),
                pe_ratio_min/max (float), revenue_growth_min (float),
                dividend_yield_min (float).
            sort_by: Optional field name to sort results by (descending).
            limit: Maximum number of results to return (default 20).

        Returns:
            List of stock info dicts that match the filters.
        """
        matches: list[dict[str, Any]] = []

        for ticker in self.universe:
            info = self._get_stock_info(ticker)
            if info is None:
                continue
            if self._matches_filters(info, filters):
                matches.append(info)

        # Sort if requested (descending by default — largest first)
        if sort_by and matches:
            matches.sort(
                key=lambda x: x.get(sort_by) if x.get(sort_by) is not None else float("-inf"),
                reverse=True,
            )

        return matches[:limit]
