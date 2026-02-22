from mcp.server.fastmcp import FastMCP

from finagent.tools.financial_data import financial_data as _financial_data
from finagent.tools.market_news import market_news as _market_news

mcp = FastMCP(
    "finagent",
    instructions="Financial analysis MCP server: stock data, SEC filings, market news, and screening.",
)


@mcp.tool()
def financial_data(
    ticker: str,
    data_type: str,
    period: str = "annual",
    limit: int = 4,
) -> str:
    """Retrieve financial data for a stock ticker.

    Args:
        ticker: Stock ticker symbol (e.g. "AAPL", "MSFT").
        data_type: One of: quote, income_statement, balance_sheet,
            cash_flow, analyst_estimates, insider_trades, key_ratios.
        period: Reporting period — "annual" or "quarterly" (default "annual").
        limit: Maximum number of periods to return (default 4).

    Returns:
        JSON string with the requested data or an error object.
    """
    return _financial_data(ticker, data_type, period, limit)


@mcp.tool()
def market_news(
    query: str,
    ticker: str | None = None,
    days_back: int = 7,
) -> str:
    """Fetch recent market news articles filtered by keyword.

    Args:
        query: Keyword to search for in article titles (e.g. "earnings",
            "Federal Reserve", "AI").
        ticker: Optional stock ticker to narrow results to a specific
            company (e.g. "AAPL", "TSLA").  When omitted the search
            scans broad-market index ETFs (SPY, QQQ, DIA).
        days_back: Number of days of history to consider (default 7).

    Returns:
        JSON string containing a list of article objects with keys:
        title, source, link, published, type, related_tickers.
    """
    return _market_news(query, ticker, days_back)


def main():
    """Entry point for stdio transport."""
    mcp.run()


if __name__ == "__main__":
    main()
