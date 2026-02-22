# FinAgent

Financial analysis MCP server for any MCP-compatible AI app (Claude, ChatGPT, Cursor, Copilot, and more).

Get live stock data, read SEC filings, search market news, and screen stocks — all from your AI assistant.

## Tools

| Tool | Tier | Description |
|------|------|-------------|
| `financial_data` | Free | Stock quotes, income statements, balance sheets, cash flow, analyst estimates, insider trades, key ratios |
| `market_news` | Free | Financial news, analyst reactions, market sentiment |
| `sec_filings` | Pro | SEC 10-K, 10-Q, 8-K filing reader with section extraction |
| `stock_screener` | Pro | Screen stocks by P/E, market cap, revenue growth, sector, and more |

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
      "command": "finagent",
      "env": {
        "FINAGENT_LICENSE_KEY": "your-key-here"
      }
    }
  }
}
```

The license key is optional — free tools work without it.

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
- "Pull the risk factors from Meta's latest 10-K" (Pro)
- "Find me tech stocks with P/E under 20 and revenue growth over 10%" (Pro)

## Get FinAgent Pro

Unlock SEC filings and stock screening at [mcp-marketplace.io/server/finagent](https://mcp-marketplace.io/server/finagent).

## Data Sources

- **Market data:** Yahoo Finance (free, real-time)
- **SEC filings:** SEC EDGAR (free, official government data)
- **News:** Yahoo Finance news feed (free)
