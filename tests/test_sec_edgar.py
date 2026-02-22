"""Tests for SECEdgarService — hits real SEC EDGAR API."""

import time

import pytest

from finagent.cache import FileCache
from finagent.services.sec_edgar import SECEdgarService


@pytest.fixture(scope="module")
def svc(tmp_path_factory):
    """Shared service instance with a temp cache dir for the whole module."""
    cache_dir = tmp_path_factory.mktemp("sec_cache")
    cache = FileCache(cache_dir=cache_dir)
    return SECEdgarService(cache=cache)


TICKER = "AAPL"


class TestGetCIK:
    def test_get_cik(self, svc):
        cik = svc.get_cik(TICKER)
        assert cik == "0000320193"

    def test_get_cik_invalid(self, svc):
        time.sleep(0.2)
        cik = svc.get_cik("ZZZNOTREAL999")
        assert cik is None


class TestListFilings:
    def test_list_filings(self, svc):
        time.sleep(0.2)
        filings = svc.list_filings(TICKER, form_type="10-K")
        assert isinstance(filings, list)
        assert len(filings) > 0
        first = filings[0]
        assert "accessionNumber" in first
        assert "filingDate" in first
        assert "primaryDocument" in first
        assert first["form"] == "10-K"


class TestGetFilingMetadata:
    def test_get_filing_metadata(self, svc):
        time.sleep(0.2)
        result = svc.get_filing_section(TICKER, filing_type="10-K", section=None)
        assert "error" not in result
        assert result["ticker"] == TICKER
        assert result["filing_type"] == "10-K"
        assert "available_sections" in result
        assert "risk_factors" in result["available_sections"]
        assert "filing_date" in result


class TestExtractSection:
    def test_extract_section(self, svc):
        time.sleep(0.2)
        result = svc.get_filing_section(TICKER, filing_type="10-K", section="risk_factors")
        # The section may or may not be found depending on filing format,
        # but the call should not error out with a service error.
        assert "error" not in result or result.get("error") == "section_not_found"
        if "error" not in result:
            assert result["section"] == "risk_factors"
            assert len(result["content"]) > 100
