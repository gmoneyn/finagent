"""Market data service wrapping yfinance."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd
import yfinance as yf

from finagent.cache import FileCache

logger = logging.getLogger(__name__)

# Cache TTL constants (seconds)
TTL_FINANCIALS = 86400   # 24 hours
TTL_ANALYST = 3600       # 1 hour
TTL_INSIDER = 21600      # 6 hours


class MarketDataService:
    """Wraps yfinance to provide structured financial data with caching."""

    def __init__(self, cache: FileCache | None = None):
        self.cache = cache or FileCache()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ticker(self, symbol: str) -> yf.Ticker:
        return yf.Ticker(symbol.upper().strip())

    def _is_valid(self, info: dict[str, Any]) -> bool:
        """Return False when yfinance returns a stub for an invalid ticker."""
        # Invalid tickers return {'trailingPegRatio': None} or similar
        # minimal dicts with no real data.
        if not info:
            return False
        # A valid ticker always has a 'currentPrice' or at least 'regularMarketPrice'
        if "currentPrice" not in info and "regularMarketPrice" not in info:
            return False
        return True

    def _invalid_ticker_error(self, ticker: str) -> dict[str, str]:
        return {
            "error": "invalid_ticker",
            "message": f"No data found for ticker '{ticker}'. It may be delisted or invalid.",
        }

    @staticmethod
    def _df_to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
        """Convert a yfinance financial-statement DataFrame to a list of dicts.

        yfinance returns statements with dates as columns and metrics as rows.
        We transpose so each dict represents one period (date).
        """
        if df is None or df.empty:
            return []

        records: list[dict[str, Any]] = []
        for col in df.columns:
            period_data: dict[str, Any] = {"date": str(col.date()) if hasattr(col, "date") else str(col)}
            for metric in df.index:
                value = df.loc[metric, col]
                # Convert numpy/pandas types to Python native
                if pd.isna(value):
                    period_data[metric] = None
                else:
                    try:
                        period_data[metric] = float(value)
                    except (ValueError, TypeError):
                        period_data[metric] = str(value)
            records.append(period_data)
        return records

    def _cached_get(self, key: str, ttl: int, fetcher) -> Any:
        """Return cached value or call fetcher, cache result, and return it."""
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        result = fetcher()
        self.cache.set(key, result, ttl_seconds=ttl)
        return result

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_quote(self, ticker: str) -> dict[str, Any]:
        """Get current quote data for a ticker. Never cached (real-time)."""
        t = self._ticker(ticker)
        info = t.info

        if not self._is_valid(info):
            return self._invalid_ticker_error(ticker)

        return {
            "ticker": ticker.upper().strip(),
            "price": info.get("currentPrice"),
            "previous_close": info.get("previousClose"),
            "open": info.get("open"),
            "day_high": info.get("dayHigh"),
            "day_low": info.get("dayLow"),
            "volume": info.get("volume"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "dividend_yield": info.get("dividendYield"),
            "52_week_high": info.get("fiftyTwoWeekHigh"),
            "52_week_low": info.get("fiftyTwoWeekLow"),
            "currency": info.get("currency"),
            "exchange": info.get("exchange"),
            "name": info.get("shortName"),
        }

    def get_income_statement(self, ticker: str) -> dict[str, Any] | list[dict[str, Any]]:
        """Get income statement data (annual). Cached for 24 hours."""
        t = self._ticker(ticker)
        info = t.info
        if not self._is_valid(info):
            return self._invalid_ticker_error(ticker)

        cache_key = f"income_statement:{ticker.upper()}"

        def fetch():
            return self._df_to_records(t.income_stmt)

        return self._cached_get(cache_key, TTL_FINANCIALS, fetch)

    def get_balance_sheet(self, ticker: str) -> dict[str, Any] | list[dict[str, Any]]:
        """Get balance sheet data (annual). Cached for 24 hours."""
        t = self._ticker(ticker)
        info = t.info
        if not self._is_valid(info):
            return self._invalid_ticker_error(ticker)

        cache_key = f"balance_sheet:{ticker.upper()}"

        def fetch():
            return self._df_to_records(t.balance_sheet)

        return self._cached_get(cache_key, TTL_FINANCIALS, fetch)

    def get_cash_flow(self, ticker: str) -> dict[str, Any] | list[dict[str, Any]]:
        """Get cash flow statement data (annual). Cached for 24 hours."""
        t = self._ticker(ticker)
        info = t.info
        if not self._is_valid(info):
            return self._invalid_ticker_error(ticker)

        cache_key = f"cash_flow:{ticker.upper()}"

        def fetch():
            return self._df_to_records(t.cashflow)

        return self._cached_get(cache_key, TTL_FINANCIALS, fetch)

    def get_analyst_estimates(self, ticker: str) -> dict[str, Any]:
        """Get analyst estimates and recommendations. Cached for 1 hour."""
        t = self._ticker(ticker)
        info = t.info
        if not self._is_valid(info):
            return self._invalid_ticker_error(ticker)

        cache_key = f"analyst_estimates:{ticker.upper()}"

        def fetch():
            result: dict[str, Any] = {"ticker": ticker.upper().strip()}

            # Price targets
            try:
                targets = t.analyst_price_targets
                if targets:
                    result["price_targets"] = targets
            except Exception:
                result["price_targets"] = None

            # Recommendations summary
            try:
                rec = t.recommendations
                if rec is not None and not rec.empty:
                    result["recommendations"] = rec.to_dict(orient="records")
                else:
                    result["recommendations"] = []
            except Exception:
                result["recommendations"] = []

            # Earnings estimates
            try:
                ee = t.earnings_estimate
                if ee is not None and not ee.empty:
                    result["earnings_estimate"] = ee.reset_index().to_dict(orient="records")
                else:
                    result["earnings_estimate"] = []
            except Exception:
                result["earnings_estimate"] = []

            # Revenue estimates
            try:
                re_est = t.revenue_estimate
                if re_est is not None and not re_est.empty:
                    result["revenue_estimate"] = re_est.reset_index().to_dict(orient="records")
                else:
                    result["revenue_estimate"] = []
            except Exception:
                result["revenue_estimate"] = []

            return result

        return self._cached_get(cache_key, TTL_ANALYST, fetch)

    def get_insider_trades(self, ticker: str) -> dict[str, Any]:
        """Get insider trading activity. Cached for 6 hours."""
        t = self._ticker(ticker)
        info = t.info
        if not self._is_valid(info):
            return self._invalid_ticker_error(ticker)

        cache_key = f"insider_trades:{ticker.upper()}"

        def fetch():
            result: dict[str, Any] = {"ticker": ticker.upper().strip()}

            # Insider transactions
            try:
                txns = t.insider_transactions
                if txns is not None and not txns.empty:
                    result["transactions"] = txns.to_dict(orient="records")
                else:
                    result["transactions"] = []
            except Exception:
                result["transactions"] = []

            # Insider purchases summary
            try:
                purchases = t.insider_purchases
                if purchases is not None and not purchases.empty:
                    result["purchases_summary"] = purchases.to_dict(orient="records")
                else:
                    result["purchases_summary"] = []
            except Exception:
                result["purchases_summary"] = []

            return result

        return self._cached_get(cache_key, TTL_INSIDER, fetch)

    def get_key_ratios(self, ticker: str) -> dict[str, Any]:
        """Get key financial ratios. Never cached (derived from quote info)."""
        t = self._ticker(ticker)
        info = t.info

        if not self._is_valid(info):
            return self._invalid_ticker_error(ticker)

        return {
            "ticker": ticker.upper().strip(),
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "peg_ratio": info.get("trailingPegRatio"),
            "price_to_book": info.get("priceToBook"),
            "price_to_sales": info.get("priceToSalesTrailing12Months"),
            "ev_to_ebitda": info.get("enterpriseToEbitda"),
            "ev_to_revenue": info.get("enterpriseToRevenue"),
            "profit_margin": info.get("profitMargins"),
            "operating_margin": info.get("operatingMargins"),
            "return_on_equity": info.get("returnOnEquity"),
            "return_on_assets": info.get("returnOnAssets"),
            "debt_to_equity": info.get("debtToEquity"),
            "current_ratio": info.get("currentRatio"),
            "quick_ratio": info.get("quickRatio"),
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
            "dividend_yield": info.get("dividendYield"),
            "payout_ratio": info.get("payoutRatio"),
            "beta": info.get("beta"),
        }
