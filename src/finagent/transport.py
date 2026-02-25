"""Transport entry points for FinAgent MCP server."""

from finagent.server import mcp


def run_stdio():
    """Run FinAgent with stdio transport."""
    mcp.run(transport="stdio")


def run_http(host: str = "0.0.0.0", port: int = 8080):
    """Run FinAgent with Streamable HTTP transport."""
    mcp.settings.host = host
    mcp.settings.port = port
    mcp.run(transport="streamable-http")
