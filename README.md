# FinAgent

Free financial analysis MCP server for any MCP-compatible AI app (Claude, ChatGPT, Cursor, Copilot, and more).

Get live stock data and market news — all from your AI assistant.

## Tools

| Tool | Description |
|------|-------------|
| `financial_data` | Stock quotes, income statements, balance sheets, cash flow, analyst estimates, insider trades, key ratios |
| `market_news` | Financial news, analyst reactions, market sentiment |

## Quick Start

### Install

```bash
pip install finagent
```

### Add to your MCP config

```json
{
  "mcpServers": {
    "finagent": {
      "command": "finagent"
    }
  }
}
```

### Run as HTTP server

```bash
finagent --http --port 8080
```

## Examples

Ask your AI assistant:

- "What's NVIDIA's current stock price and P/E ratio?"
- "Show me Apple's last 4 quarters of revenue"
- "Who's been buying or selling TSLA stock lately?"
- "What are analysts saying about AMZN?"

## Want More?

**FinAgent Pro** adds SEC filing analysis and stock screening. Get it at [mcp-marketplace.io/server/finagent-pro](https://mcp-marketplace.io/server/finagent-pro).

## Data Sources

- **Market data:** Yahoo Finance (free, real-time)
- **News:** Yahoo Finance news feed (free)
