"""SEC EDGAR service — access SEC filings, extract sections, with caching."""

from __future__ import annotations

import logging
import re
import time
from typing import Any

import requests

from finagent.cache import FileCache

logger = logging.getLogger(__name__)

# Cache TTL constants (seconds)
TTL_TICKER_MAP = 86400      # 24 hours
TTL_SUBMISSIONS = 86400     # 24 hours
TTL_FILING = None           # Forever — filings are immutable

# SEC rate-limit: minimum delay between requests (seconds)
_MIN_REQUEST_INTERVAL = 0.15

# Maximum content length returned to caller
_MAX_CONTENT_CHARS = 30_000

# Supported filing types
SUPPORTED_FORM_TYPES = ("10-K", "10-Q", "8-K", "DEF-14A")

# Section extraction regex patterns for 10-K filings.
# Each maps a section name to (start_pattern, end_pattern).
_SECTION_PATTERNS: dict[str, tuple[str, str]] = {
    "business_overview": (
        r"(?i)>\s*Item\s+1[\.\s]*[^A-Za-z0-9]*Business",
        r"(?i)>\s*Item\s+1A|>\s*Item\s+2",
    ),
    "risk_factors": (
        r"(?i)>\s*Item\s+1A[\.\s]*[^A-Za-z0-9]*Risk\s+Factors",
        r"(?i)>\s*Item\s+1B|>\s*Item\s+2",
    ),
    "item_7": (
        r"(?i)>\s*Item\s+7[\.\s]*[^A-Za-z0-9]*Management",
        r"(?i)>\s*Item\s+7A|>\s*Item\s+8",
    ),
    "item_7a": (
        r"(?i)>\s*Item\s+7A",
        r"(?i)>\s*Item\s+8",
    ),
    "financial_statements": (
        r"(?i)>\s*Item\s+8",
        r"(?i)>\s*Item\s+9",
    ),
}


class SECEdgarService:
    """Wraps SEC EDGAR APIs to fetch and parse company filings."""

    BASE_URL = "https://data.sec.gov"
    ARCHIVES_URL = "https://www.sec.gov/Archives/edgar/data"
    TICKER_URL = "https://www.sec.gov/files/company_tickers.json"

    def __init__(
        self,
        email: str = "finagent@example.com",
        cache: FileCache | None = None,
    ):
        self.cache = cache or FileCache()
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": f"FinAgent {email}",
            "Accept-Encoding": "gzip, deflate",
        })
        self._last_request_time: float = 0.0

    # ------------------------------------------------------------------
    # Rate limiting
    # ------------------------------------------------------------------

    def _rate_limit(self) -> None:
        """Ensure minimum interval between SEC requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < _MIN_REQUEST_INTERVAL:
            time.sleep(_MIN_REQUEST_INTERVAL - elapsed)
        self._last_request_time = time.time()

    def _get(self, url: str) -> requests.Response:
        """Issue a rate-limited GET request."""
        self._rate_limit()
        resp = self._session.get(url, timeout=30)
        resp.raise_for_status()
        return resp

    # ------------------------------------------------------------------
    # CIK lookup
    # ------------------------------------------------------------------

    def _load_ticker_map(self) -> dict[str, str]:
        """Load ticker -> CIK mapping from SEC, cached for 24h."""
        cache_key = "sec:ticker_map"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        resp = self._get(self.TICKER_URL)
        raw = resp.json()

        # raw is {index: {cik_str, ticker, title}}
        ticker_map: dict[str, str] = {}
        for entry in raw.values():
            ticker = entry["ticker"].upper()
            cik = str(entry["cik_str"]).zfill(10)
            ticker_map[ticker] = cik

        self.cache.set(cache_key, ticker_map, ttl_seconds=TTL_TICKER_MAP)
        return ticker_map

    def get_cik(self, ticker: str) -> str | None:
        """Return zero-padded 10-digit CIK for a ticker, or None."""
        ticker_map = self._load_ticker_map()
        return ticker_map.get(ticker.upper().strip())

    # ------------------------------------------------------------------
    # List filings
    # ------------------------------------------------------------------

    def list_filings(
        self,
        ticker: str,
        form_type: str = "10-K",
        count: int = 10,
    ) -> list[dict[str, Any]]:
        """Return recent filings for a ticker filtered by form type.

        Each filing dict contains: accessionNumber, filingDate, primaryDocument, form.
        """
        cik = self.get_cik(ticker)
        if cik is None:
            return []

        cache_key = f"sec:submissions:{cik}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            submissions = cached
        else:
            url = f"{self.BASE_URL}/submissions/CIK{cik}.json"
            resp = self._get(url)
            submissions = resp.json()
            self.cache.set(cache_key, submissions, ttl_seconds=TTL_SUBMISSIONS)

        recent = submissions.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        accessions = recent.get("accessionNumber", [])
        dates = recent.get("filingDate", [])
        docs = recent.get("primaryDocument", [])

        results: list[dict[str, Any]] = []
        for i, form in enumerate(forms):
            if form == form_type:
                results.append({
                    "accessionNumber": accessions[i],
                    "filingDate": dates[i],
                    "primaryDocument": docs[i],
                    "form": form,
                })
                if len(results) >= count:
                    break

        return results

    # ------------------------------------------------------------------
    # Download filing HTML
    # ------------------------------------------------------------------

    def _filing_url(self, cik: str, accession: str, document: str) -> str:
        """Build the full URL to a filing document."""
        acc_no_dash = accession.replace("-", "")
        return f"{self.ARCHIVES_URL}/{cik.lstrip('0')}/{acc_no_dash}/{document}"

    def download_filing(self, cik: str, accession: str, document: str) -> str:
        """Download the raw HTML text of a filing, cached forever."""
        cache_key = f"sec:filing:{accession}:{document}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            # Cached value is a dict with a "html" key
            return cached["html"]

        url = self._filing_url(cik, accession, document)
        resp = self._get(url)
        html = resp.text

        self.cache.set(cache_key, {"html": html}, ttl_seconds=TTL_FILING)
        return html

    # ------------------------------------------------------------------
    # Section extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _strip_html(html: str) -> str:
        """Crude HTML tag removal for readable text."""
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"&nbsp;", " ", text)
        text = re.sub(r"&amp;", "&", text)
        text = re.sub(r"&lt;", "<", text)
        text = re.sub(r"&gt;", ">", text)
        text = re.sub(r"&#\d+;", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def extract_section(html: str, section: str) -> str | None:
        """Extract a named section from a 10-K HTML filing.

        Returns plain text of the section or None if not found.
        """
        patterns = _SECTION_PATTERNS.get(section)
        if patterns is None:
            return None

        start_pat, end_pat = patterns

        start_match = re.search(start_pat, html)
        if start_match is None:
            return None

        remainder = html[start_match.start():]
        end_match = re.search(end_pat, remainder[1:])  # skip first char to avoid self-match
        if end_match is None:
            chunk = remainder[:200_000]  # safety cap
        else:
            chunk = remainder[: end_match.start() + 1]

        text = SECEdgarService._strip_html(chunk)
        return text if text else None

    # ------------------------------------------------------------------
    # High-level API
    # ------------------------------------------------------------------

    def get_filing_section(
        self,
        ticker: str,
        filing_type: str = "10-K",
        section: str | None = None,
        date_range: str | None = None,
    ) -> dict[str, Any]:
        """Retrieve a SEC filing section for a company.

        Args:
            ticker: Stock ticker symbol (e.g. "AAPL").
            filing_type: SEC form type — "10-K", "10-Q", "8-K", "DEF-14A".
            section: Section to extract (10-K only). One of:
                business_overview, risk_factors, item_7, item_7a,
                financial_statements.  If None, returns metadata with
                available sections.
            date_range: Optional date filter (not yet implemented, reserved).

        Returns:
            Dict with filing metadata and optionally the extracted section text.
        """
        ticker = ticker.upper().strip()

        if filing_type not in SUPPORTED_FORM_TYPES:
            return {
                "error": "invalid_filing_type",
                "message": (
                    f"Unsupported filing type '{filing_type}'. "
                    f"Supported: {', '.join(SUPPORTED_FORM_TYPES)}"
                ),
            }

        cik = self.get_cik(ticker)
        if cik is None:
            return {
                "error": "unknown_ticker",
                "message": f"Could not find CIK for ticker '{ticker}'.",
            }

        filings = self.list_filings(ticker, form_type=filing_type, count=5)
        if not filings:
            return {
                "error": "no_filings",
                "message": f"No {filing_type} filings found for {ticker}.",
            }

        # Use the most recent filing
        filing = filings[0]

        if section is None:
            # Return metadata only
            available = list(_SECTION_PATTERNS.keys()) if filing_type == "10-K" else []
            return {
                "ticker": ticker,
                "filing_type": filing_type,
                "filing_date": filing["filingDate"],
                "accession_number": filing["accessionNumber"],
                "available_sections": available,
                "recent_filings": [
                    {"filing_date": f["filingDate"], "accession_number": f["accessionNumber"]}
                    for f in filings
                ],
            }

        # Download and extract section
        html = self.download_filing(cik, filing["accessionNumber"], filing["primaryDocument"])
        content = self.extract_section(html, section)

        if content is None:
            return {
                "error": "section_not_found",
                "message": (
                    f"Could not extract section '{section}' from {ticker} {filing_type} "
                    f"filed {filing['filingDate']}. The filing format may not match "
                    f"expected patterns."
                ),
                "available_sections": list(_SECTION_PATTERNS.keys()),
            }

        truncated = False
        if len(content) > _MAX_CONTENT_CHARS:
            content = content[:_MAX_CONTENT_CHARS]
            truncated = True

        result: dict[str, Any] = {
            "ticker": ticker,
            "filing_type": filing_type,
            "filing_date": filing["filingDate"],
            "section": section,
            "content": content,
        }

        if truncated:
            result["note"] = (
                f"Content truncated to {_MAX_CONTENT_CHARS:,} characters. "
                "The full section is longer."
            )

        return result
