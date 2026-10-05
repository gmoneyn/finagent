"""Tests for the market_news tool function — hits real yfinance API."""

import json

import pytest

from finagent.tools.market_news import market_news


class TestMarketNewsWithTicker:
    def test_market_news_with_ticker(self):
        raw = market_news(query="earnings", ticker="AAPL")
        result = json.loads(raw)
        assert isinstance(result, list)


class TestMarketNewsQueryOnly:
    def test_market_news_query_only(self):
        raw = market_news(query="Federal Reserve")
        result = json.loads(raw)
        assert isinstance(result, list)
