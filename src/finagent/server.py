from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "finagent",
    instructions="Financial analysis MCP server: stock data, SEC filings, market news, and screening.",
)


def main():
    """Entry point for stdio transport."""
    mcp.run()


if __name__ == "__main__":
    main()
