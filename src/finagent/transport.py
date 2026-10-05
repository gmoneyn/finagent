"""Transport entry points for FinAgent MCP server."""

import os
import sys

from mcp.server.transport_security import TransportSecuritySettings

from finagent.server import mcp

LOOPBACK_HOSTS = ("127.0.0.1", "localhost", "::1")


def run_stdio():
    """Run FinAgent with stdio transport."""
    mcp.run(transport="stdio")


def run_http(host: str = "127.0.0.1", port: int = 8080):
    """Run FinAgent with Streamable HTTP transport.

    Binds loopback by default. Any other host is an explicit choice and needs
    MCP_ALLOWED_HOSTS: without it the server refuses to start.
    """
    if host not in LOOPBACK_HOSTS:
        allowed = [h.strip() for h in os.environ.get("MCP_ALLOWED_HOSTS", "").split(",") if h.strip()]
        if not allowed:
            sys.exit(
                f"[mcp] REFUSING TO START: binding {host} requires MCP_ALLOWED_HOSTS "
                "(comma-separated Host values), otherwise Host/Origin validation is disabled "
                "and the server is exposed to DNS-rebinding. Example: MCP_ALLOWED_HOSTS=my.host,localhost"
            )
        mcp.settings.transport_security = TransportSecuritySettings(allowed_hosts=allowed)
    mcp.settings.host = host
    mcp.settings.port = port
    mcp.run(transport="streamable-http")
