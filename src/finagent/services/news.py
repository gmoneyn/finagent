"""News aggregation service wrapping yfinance news feeds."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import yfinance as yf

logger = logging.getLogger(__name__)

# Broad-market ETFs used as fallback when searching by query only.
_INDEX_ETFS = ("SPY", "QQQ", "DIA")


class NewsService:
    """Fetches and normalises news articles from yfinance."""

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_article(raw: dict) -> dict:
        """Normalise a single yfinance news item into a flat dict.

        yfinance >= 0.2.31 returns items shaped as:
            {"id": ..., "content": {"title": ..., "provider": {...}, ...}}
        We extract the useful fields into a consistent structure.
        """
        content = raw.get("content", raw)

        title = content.get("title", "")
        provider = content.get("provider", {})
        source = provider.get("displayName", "") if isinstance(provider, dict) else str(provider)

        # Build the link from canonicalUrl or clickThroughUrl
        link = ""
        for url_key in ("canonicalUrl", "clickThroughUrl"):
            url_obj = content.get(url_key)
            if isinstance(url_obj, dict) and url_obj.get("url"):
                link = url_obj["url"]
                break
            elif isinstance(url_obj, str) and url_obj:
                link = url_obj
                break

        # Publish time
        published = content.get("pubDate", content.get("providerPublishTime", ""))

        content_type = content.get("contentType", "STORY")

        return {
            "title": title,
            "source": source,
            "link": link,
            "published": published,
            "type": content_type,
            "related_tickers": [],
        }

    @staticmethod
    def _matches_query(article: dict, query: str) -> bool:
        """Return True if *query* appears (case-insensitive) in the article title."""
        if not query:
            return True
        return query.lower() in article.get("title", "").lower()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_news(
        self,
        ticker: str | None = None,
        query: str | None = None,
        days_back: int = 7,
    ) -> list[dict]:
        """Fetch news articles, optionally filtered by ticker and/or keyword.

        Args:
            ticker: Stock symbol to pull news for (e.g. "AAPL").
            query: Keyword filter applied to article titles.
            days_back: How many days of history to consider (not all
                providers honour this — we rely on yfinance's default
                feed window and post-filter when possible).

        Returns:
            A list of article dicts with keys: title, source, link,
            published, type, related_tickers.  Returns an empty list
            on any error or when neither *ticker* nor *query* is given.
        """
        if not ticker and not query:
            return []

        try:
            if ticker:
                return self._news_for_ticker(ticker, query)
            else:
                return self._news_for_query(query)  # type: ignore[arg-type]
        except Exception:
            logger.exception("Failed to fetch news (ticker=%s, query=%s)", ticker, query)
            return []

    # ------------------------------------------------------------------
    # Private fetch helpers
    # ------------------------------------------------------------------

    def _news_for_ticker(self, ticker: str, query: str | None) -> list[dict]:
        """Pull news for a specific ticker, optionally keyword-filtered."""
        raw_news = yf.Ticker(ticker.upper().strip()).news
        if not isinstance(raw_news, list):
            return []

        articles = [self._parse_article(item) for item in raw_news]

        if query:
            articles = [a for a in articles if self._matches_query(a, query)]

        return articles

    def _news_for_query(self, query: str) -> list[dict]:
        """Search broad-market ETFs for articles matching *query*."""
        seen_titles: set[str] = set()
        results: list[dict] = []

        for symbol in _INDEX_ETFS:
            try:
                raw_news = yf.Ticker(symbol).news
                if not isinstance(raw_news, list):
                    continue
                for item in raw_news:
                    article = self._parse_article(item)
                    if self._matches_query(article, query) and article["title"] not in seen_titles:
                        seen_titles.add(article["title"])
                        results.append(article)
            except Exception:
                logger.debug("Failed to fetch news for fallback ticker %s", symbol)
                continue

        return results
