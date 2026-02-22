"""Tests for the stock_screener MCP tool."""

import json

import pytest

from finagent.tools.stock_screener import stock_screener


class TestLicenseGating:
    def test_screener_blocked_without_license(self, monkeypatch):
        monkeypatch.delenv("FINAGENT_LICENSE_KEY", raising=False)
        result = stock_screener({"sector": "Technology"}, limit=3)
        data = json.loads(result)
        assert data["error"] == "premium_required"


class TestWithLicense:
    def test_screener_works_with_license(self, monkeypatch):
        monkeypatch.setenv("FINAGENT_LICENSE_KEY", "test-key-123")
        result = stock_screener({"sector": "Technology"}, limit=3)
        data = json.loads(result)
        assert isinstance(data, list)
        # Should return some results (at least 1 tech stock in default universe)
        assert len(data) >= 1
        assert len(data) <= 3
        for stock in data:
            assert "ticker" in stock
            assert "name" in stock
            assert "sector" in stock
