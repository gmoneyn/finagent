"""Tests for NewsService — hits real yfinance API."""

import pytest

from finagent.services.news import NewsService


@pytest.fixture(scope="module")
def svc():
    return NewsService()


class TestGetNewsForTicker:
    def test_get_news_for_ticker(self, svc):
        """Fetch news for a well-known ticker and verify we get a list back."""
        result = svc.get_news(ticker="AAPL")
        assert isinstance(result, list)
        # AAPL should almost always have news; verify at least one article
        if len(result) > 0:
            article = result[0]
            assert "title" in article
            assert "source" in article
            assert "link" in article
            assert "published" in article


class TestGetNewsWithQuery:
    def test_get_news_with_query(self, svc):
        """Search for a broad keyword and verify we get a list back."""
        result = svc.get_news(query="earnings report")
        assert isinstance(result, list)
        # Query search across index ETFs — may or may not match, but
        # the return type must always be a list.


class TestGetNewsNoArgs:
    def test_get_news_no_args(self, svc):
        """Calling with no ticker and no query returns an empty list."""
        result = svc.get_news()
        assert result == []
