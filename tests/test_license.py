"""Tests for the license gating module."""

import os

from finagent.license import check_license, require_license


class TestCheckLicense:
    def test_no_license_key(self, monkeypatch):
        monkeypatch.delenv("FINAGENT_LICENSE_KEY", raising=False)
        result = check_license()
        assert result["valid"] is False

    def test_license_key_present(self, monkeypatch):
        monkeypatch.setenv("FINAGENT_LICENSE_KEY", "test-key-123")
        result = check_license()
        assert result["valid"] is True


class TestRequireLicense:
    def test_require_returns_error_without_key(self, monkeypatch):
        monkeypatch.delenv("FINAGENT_LICENSE_KEY", raising=False)
        result = require_license("sec_filings")
        assert result is not None
        assert "premium_required" in result

    def test_require_returns_none_with_key(self, monkeypatch):
        monkeypatch.setenv("FINAGENT_LICENSE_KEY", "test-key-123")
        result = require_license("sec_filings")
        assert result is None
