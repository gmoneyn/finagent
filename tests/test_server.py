"""Integration test -- verify server has all tools registered."""

from finagent.server import mcp

EXPECTED_TOOLS = {"financial_data", "market_news"}


def test_server_has_all_tools():
    """Every registered tool name must be present."""
    registered = set(mcp._tool_manager._tools.keys())
    assert registered == EXPECTED_TOOLS, (
        f"Registered tools {registered} != expected {EXPECTED_TOOLS}"
    )


def test_server_name():
    assert mcp.name == "finagent"
