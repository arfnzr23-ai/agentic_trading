# Hyperliquid MCP Server Walkthrough

I have successfully built, optimized, and verified the Hyperliquid MCP Server. This server is now a robust "Trading OS" for AI agents, featuring smart order management, risk intelligence, and safety mechanisms.

## Key Features

- **Smart Trading**: Trade by USD amount (`place_order_usd`) or Portfolio % (`place_order_pct`) with automatic precision handling.
- **Risk Intelligence**: Instant access to account health (`get_account_health`), position risk (`get_position_risk`), and market context (`get_market_leaders`).
- **Safety First**: "Panic" buttons to cancel all orders or close all positions instantly.
- **Debugging**: Integrated MCP Inspector support for interactive testing.
- **Logging**: Human-readable `agent_actions.log` tracks every move.

## Setup & Usage

### 1. Prerequisites

- Python 3.10+
- A Hyperliquid account with API keys.
- `.env` file with `HL_WL` (Wallet Address) and `HL_PK` (Private Key).

### 2. Installation

```bash
pip install -r requirements.txt
```

### 3. Running the Server

To start the MCP server:

```bash
python server.py
```

## Optimized Toolset

I have streamlined the API to focus on high-value tools and optimized internal logic (consolidated precision handling, removed duplicates).

### Consolidated Analysis Tools

- **`get_token_analytics(coin, interval="4h")`**: Comprehensive technical analysis including Price, Volatility, Trend (ADX), Key Levels (Swings), RSI, EMA, and Funding Rate.
- **`get_order_book_analytics(coin)`**: Deep order book analysis including Imbalance, Liquidation Walls, and Premia.
- **`get_volume_profile_24h(coin)`**: Volume Profile (POC, VAH, VAL).
- **`get_correlation_matrix()`**: 24h Price Correlation.

### Smart Trading & Account

- **`place_smart_order(coin, is_buy, size, size_type="usd", ...)`**: Flexible order placement with USD/Equity % sizing and optional TP/SL.
- **`get_account_info(type="perp")`**: Consolidated account info (Perp/Spot).
- **`get_exchange_meta(type="perp")`**: Consolidated exchange metadata.
- **`transfer(amount, destination, token="USDC")`**: Consolidated transfer tool.
- **`close_position(...)`**: Close specific % of a position.
- **`get_account_health()`**: Equity, margin usage, risk level.
- **`get_market_leaders()`**: Top gainers/losers and volume.
- **`get_position_risk(coin)`**: Liquidation price, distance, PnL.
- **`get_max_trade_size(coin)`**: Max buy/sell size.

### Safety

- `cancel_all_orders()`: **PANIC** - Cancel everything.
- `close_all_positions()`: **PANIC** - Liquidate everything.

## Verification

I have verified the server using:

1. **`verify_tools.py`**: Validated all read-only and logic tools.
2. **MCP Inspector**: Manually tested tool interactions.
3. **SDK Inspection**: Confirmed alignment with official Hyperliquid Python SDK.

> [!WARNING]
> This server has access to your trading account. Ensure your private key is kept secure.
