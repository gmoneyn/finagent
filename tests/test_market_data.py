"""Tests for MarketDataService — hits real yfinance API."""

import pytest

from finagent.services.market_data import MarketDataService


@pytest.fixture(scope="module")
def svc(tmp_path_factory):
    """Shared service instance with a temp cache dir for the whole module."""
    cache_dir = tmp_path_factory.mktemp("market_cache")
    from finagent.cache import FileCache

    cache = FileCache(cache_dir=cache_dir)
    return MarketDataService(cache=cache)


TICKER = "AAPL"


class TestGetQuote:
    def test_get_quote(self, svc):
        result = svc.get_quote(TICKER)
        assert "error" not in result
        assert result["ticker"] == TICKER
        assert isinstance(result["price"], (int, float))
        assert result["price"] > 0
        assert result["name"] is not None
        # Check all expected keys are present
        expected_keys = [
            "ticker", "price", "previous_close", "open", "day_high",
            "day_low", "volume", "market_cap", "pe_ratio", "forward_pe",
            "dividend_yield", "52_week_high", "52_week_low", "currency",
            "exchange", "name",
        ]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"


class TestIncomeStatement:
    def test_get_income_statement(self, svc):
        result = svc.get_income_statement(TICKER)
        assert isinstance(result, list)
        assert len(result) > 0
        # Each record should have a date and at least some financial metrics
        first = result[0]
        assert "date" in first
        assert len(first) > 1  # date + at least one metric


class TestBalanceSheet:
    def test_get_balance_sheet(self, svc):
        result = svc.get_balance_sheet(TICKER)
        assert isinstance(result, list)
        assert len(result) > 0
        first = result[0]
        assert "date" in first
        assert len(first) > 1


class TestCashFlow:
    def test_get_cash_flow(self, svc):
        result = svc.get_cash_flow(TICKER)
        assert isinstance(result, list)
        assert len(result) > 0
        first = result[0]
        assert "date" in first
        assert len(first) > 1


class TestAnalystEstimates:
    def test_get_analyst_estimates(self, svc):
        result = svc.get_analyst_estimates(TICKER)
        assert "error" not in result
        assert result["ticker"] == TICKER
        # Should have at least price_targets and recommendations
        assert "price_targets" in result
        assert "recommendations" in result
        # Price targets should be a dict with 'mean' or similar
        if result["price_targets"]:
            assert isinstance(result["price_targets"], dict)


class TestInsiderTrades:
    def test_get_insider_trades(self, svc):
        result = svc.get_insider_trades(TICKER)
        assert "error" not in result
        assert result["ticker"] == TICKER
        assert "transactions" in result
        assert "purchases_summary" in result
        # AAPL should have insider transactions
        assert isinstance(result["transactions"], list)


class TestKeyRatios:
    def test_get_key_ratios(self, svc):
        result = svc.get_key_ratios(TICKER)
        assert "error" not in result
        assert result["ticker"] == TICKER
        expected_keys = [
            "pe_ratio", "forward_pe", "peg_ratio", "price_to_book",
            "price_to_sales", "ev_to_ebitda", "ev_to_revenue",
            "profit_margin", "operating_margin", "return_on_equity",
            "return_on_assets", "debt_to_equity", "current_ratio",
            "quick_ratio", "revenue_growth", "earnings_growth",
            "dividend_yield", "payout_ratio", "beta",
        ]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"
        # At least some ratios should be numeric
        assert isinstance(result["pe_ratio"], (int, float))
        assert isinstance(result["beta"], (int, float))


class TestInvalidTicker:
    def test_invalid_ticker(self, svc):
        result = svc.get_quote("INVALIDTICKER12345")
        assert result["error"] == "invalid_ticker"
        assert "message" in result
