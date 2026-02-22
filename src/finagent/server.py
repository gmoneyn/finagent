from mcp.server.fastmcp import FastMCP

from finagent.tools.financial_data import financial_data as _financial_data

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


def main():
    """Entry point for stdio transport."""
    mcp.run()


if __name__ == "__main__":
    main()
