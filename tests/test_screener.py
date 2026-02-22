"""Tests for ScreenerService — hits real yfinance API."""

import pytest

from finagent.cache import FileCache
from finagent.services.screener import ScreenerService

# Use a tiny universe to keep tests fast
TEST_UNIVERSE = ["AAPL", "MSFT", "GOOGL", "JPM", "XOM"]


@pytest.fixture(scope="module")
def svc(tmp_path_factory):
    """Shared service instance with a temp cache dir and small universe."""
    cache_dir = tmp_path_factory.mktemp("screener_cache")
    cache = FileCache(cache_dir=cache_dir)
    return ScreenerService(cache=cache, universe=TEST_UNIVERSE)


class TestScreenBySector:
    def test_screen_by_sector(self, svc):
        results = svc.screen(filters={"sector": "Technology"}, limit=3)
        assert isinstance(results, list)
        assert len(results) <= 3
        # Every result should have the basic fields
        for stock in results:
            assert "ticker" in stock
            assert "name" in stock
            assert "sector" in stock
            assert "market_cap" in stock
            assert "price" in stock
            # Sector should contain "Technology"
            assert "technology" in stock["sector"].lower()


class TestScreenEmptyResult:
    def test_screen_empty_result(self, svc):
        # Use absurdly high market_cap_min that no company meets
        results = svc.screen(
            filters={"market_cap_min": 999_999_999_999_999},
            limit=10,
        )
        assert isinstance(results, list)
        assert len(results) == 0
