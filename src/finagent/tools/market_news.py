"""market_news tool — delegates to NewsService and returns JSON."""

from __future__ import annotations

import json

from finagent.services.news import NewsService

_service = NewsService()


def market_news(
    query: str,
    ticker: str | None = None,
    days_back: int = 7,
) -> str:
    """Fetch recent market news articles.

    Args:
        query: Keyword to search for in article titles.
        ticker: Optional stock ticker to narrow the search (e.g. "AAPL").
        days_back: Number of days of history to consider (default 7).

    Returns:
        JSON string containing a list of article objects, each with keys:
        title, source, link, published, type, related_tickers.
    """
    articles = _service.get_news(ticker=ticker, query=query, days_back=days_back)
    return json.dumps(articles, default=str)
