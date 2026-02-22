from mcp.server.fastmcp import FastMCP

from finagent.tools.financial_data import financial_data as _financial_data
from finagent.tools.market_news import market_news as _market_news
from finagent.tools.sec_filings import sec_filings as _sec_filings
from finagent.tools.stock_screener import stock_screener as _stock_screener

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


@mcp.tool()
def sec_filings(
    ticker: str,
    filing_type: str = "10-K",
    section: str | None = None,
    date_range: str | None = None,
) -> str:
    """Retrieve SEC filing data for a company.

    PREMIUM FEATURE — requires a FinAgent license key
    (set FINAGENT_LICENSE_KEY env var).

    Args:
        ticker: Stock ticker symbol (e.g. "AAPL", "MSFT").
        filing_type: SEC form type — "10-K", "10-Q", "8-K", or "DEF-14A".
        section: Section to extract from a 10-K filing. One of:
            business_overview, risk_factors, item_7, item_7a,
            financial_statements.  Omit to get filing metadata and
            a list of available sections.
        date_range: Optional date filter (reserved for future use).

    Returns:
        JSON string with filing data or an error object.
    """
    return _sec_filings(ticker, filing_type, section, date_range)


@mcp.tool()
def stock_screener(
    filters: dict,
    sort_by: str | None = None,
    limit: int = 20,
) -> str:
    """Screen stocks from a curated universe by financial criteria.

    PREMIUM FEATURE — requires a FinAgent license key
    (set FINAGENT_LICENSE_KEY env var).

    Args:
        filters: Dict of filter criteria. Supported keys:
            sector (str) — filter by sector name (e.g. "Technology"),
            market_cap_min (float) — minimum market cap,
            market_cap_max (float) — maximum market cap,
            pe_ratio_min (float) — minimum trailing P/E ratio,
            pe_ratio_max (float) — maximum trailing P/E ratio,
            revenue_growth_min (float) — minimum revenue growth rate,
            dividend_yield_min (float) — minimum dividend yield.
        sort_by: Optional field name to sort results by descending
            (e.g. "market_cap", "pe_ratio", "dividend_yield").
        limit: Maximum number of results to return (default 20).

    Returns:
        JSON string with a list of matching stock objects, each containing:
        ticker, name, sector, industry, market_cap, pe_ratio, forward_pe,
        price, dividend_yield, revenue_growth, profit_margin,
        return_on_equity, beta, 52_week_high, 52_week_low.
    """
    return _stock_screener(filters, sort_by, limit)


def main():
    """Entry point for stdio transport."""
    mcp.run()


if __name__ == "__main__":
    main()
