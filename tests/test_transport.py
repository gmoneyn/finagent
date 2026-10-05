"""--http must stay on loopback unless the operator chooses otherwise."""

import sys

import pytest

from finagent import server, transport
from finagent.server import mcp


@pytest.fixture
def runs(monkeypatch):
    """Record mcp.run calls instead of starting a server; restore settings afterwards."""
    calls = []
    monkeypatch.setattr(mcp, "run", lambda **kw: calls.append(kw))
    for field in ("host", "port", "transport_security"):
        monkeypatch.setattr(mcp.settings, field, getattr(mcp.settings, field))
    return calls


def test_http_defaults_to_loopback(runs):
    transport.run_http()
    assert mcp.settings.host == "127.0.0.1"
    assert runs == [{"transport": "streamable-http"}]


def test_wide_bind_without_allowed_hosts_refuses(runs, monkeypatch):
    monkeypatch.delenv("MCP_ALLOWED_HOSTS", raising=False)
    before = mcp.settings.host
    with pytest.raises(SystemExit) as stop:
        transport.run_http(host="0.0.0.0")
    assert "REFUSING TO START" in str(stop.value) and "MCP_ALLOWED_HOSTS" in str(stop.value)
    assert stop.value.code not in (0, None)
    assert runs == [] and mcp.settings.host == before


def test_wide_bind_with_allowed_hosts_installs_the_allowlist(runs, monkeypatch):
    monkeypatch.setenv("MCP_ALLOWED_HOSTS", " a.example , b.example:8080 ,")
    transport.run_http(host="0.0.0.0", port=9000)
    assert mcp.settings.host == "0.0.0.0" and mcp.settings.port == 9000
    assert mcp.settings.transport_security.enable_dns_rebinding_protection is True
    assert mcp.settings.transport_security.allowed_hosts == ["a.example", "b.example:8080"]
    assert runs == [{"transport": "streamable-http"}]


def test_main_http_flag_alone_asks_for_loopback(monkeypatch):
    seen = []
    monkeypatch.setattr(transport, "run_http", lambda **kw: seen.append(kw))
    monkeypatch.setattr(sys, "argv", ["finagent", "--http"])
    server.main()
    assert seen == [{"host": "127.0.0.1", "port": 8080}]


def test_main_passes_an_explicit_host_through(monkeypatch):
    seen = []
    monkeypatch.setattr(transport, "run_http", lambda **kw: seen.append(kw))
    monkeypatch.setattr(sys, "argv", ["finagent", "--http", "--host", "0.0.0.0", "--port", "9000"])
    server.main()
    assert seen == [{"host": "0.0.0.0", "port": 9000}]
