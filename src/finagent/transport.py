"""Transport entry points for FinAgent MCP server."""

from finagent.server import mcp


def run_stdio():
    """Run FinAgent with stdio transport (local process)."""
    mcp.run(transport="stdio")


def run_http(host: str = "0.0.0.0", port: int = 8080):
    """Run FinAgent with Streamable HTTP transport (remote server)."""
    mcp.settings.host = host
    mcp.settings.port = port
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    import sys

    if "--http" in sys.argv:
        port = 8080
        for i, arg in enumerate(sys.argv):
            if arg == "--port" and i + 1 < len(sys.argv):
                port = int(sys.argv[i + 1])
        run_http(port=port)
    else:
        run_stdio()
