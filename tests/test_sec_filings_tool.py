"""Tests for the sec_filings MCP tool."""

import json
import time

import pytest

from finagent.tools.sec_filings import sec_filings


class TestLicenseGating:
    def test_sec_filings_blocked_without_license(self, monkeypatch):
        monkeypatch.delenv("FINAGENT_LICENSE_KEY", raising=False)
        result = sec_filings("AAPL", "10-K")
        data = json.loads(result)
        assert data["error"] == "premium_required"


class TestWithLicense:
    def test_sec_filings_metadata_with_license(self, monkeypatch):
        monkeypatch.setenv("FINAGENT_LICENSE_KEY", "test-key-123")
        time.sleep(0.2)
        result = sec_filings("AAPL", "10-K")
        data = json.loads(result)
        assert "error" not in data
        assert "available_sections" in data
        assert data["ticker"] == "AAPL"
