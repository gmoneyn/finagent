"""Tests for the financial_data tool function — hits real yfinance API."""

import json

import pytest

from finagent.tools.financial_data import financial_data


class TestFinancialDataQuote:
    def test_financial_data_quote(self):
        raw = financial_data(ticker="AAPL", data_type="quote")
        result = json.loads(raw)
        assert "error" not in result
        assert result["ticker"] == "AAPL"
        assert isinstance(result["price"], (int, float))
        assert result["price"] > 0


class TestFinancialDataIncomeStatement:
    def test_financial_data_income_statement(self):
        raw = financial_data(ticker="AAPL", data_type="income_statement", limit=2)
        result = json.loads(raw)
        assert isinstance(result, list)
        assert len(result) <= 2
        assert len(result) > 0


class TestFinancialDataInvalidType:
    def test_financial_data_invalid_type(self):
        raw = financial_data(ticker="AAPL", data_type="invalid_thing")
        result = json.loads(raw)
        assert "error" in result
        assert result["error"] == "invalid_data_type"


class TestFinancialDataInvalidTicker:
    def test_financial_data_invalid_ticker(self):
        raw = financial_data(ticker="XYZNOTREAL123", data_type="quote")
        result = json.loads(raw)
        assert "error" in result
