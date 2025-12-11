# Hyperliquid MCP Server Walkthrough

I have successfully built and verified the Hyperliquid MCP Server. This server provides tools for AI agents to interact with the Hyperliquid exchange.

## Features

- **Market Data**: Get real-time prices, order books, and historical candles.
- **Account Info**: Check account balance, margin, and positions.
- **Trading**: Place and cancel orders (Limit orders supported).

## Setup & Usage

### 1. Prerequisites

- Python 3.10+
- A Hyperliquid account with API keys.
- `.env` file with `HL_WL` (Wallet Address) and `HL_PK` (Private Key).

### 2. Installation

You can use `pip` or `uv` (recommended).

**Using UV:**

```bash
# Install uv if needed
pip install uv

# Create venv and install
uv venv
# On Windows: .venv\Scripts\activate
# On Mac/Linux: source .venv/bin/activate

uv pip install -r requirements.txt
```

**Using Pip:**

```bash
pip install -r requirements.txt
```

_Note: If you encounter issues with `aiohttp`, try installing `hyperliquid` with `--no-deps` and then installing other dependencies manually._

### 3. Running the Server

To start the MCP server:

```bash
python server.py
```

This will start the FastMCP server, which can be connected to your MCP client (e.g., Claude Desktop, or another agent).

## Tools Available

- **`get_token_analytics(coin, interval="4h")`**: Comprehensive technical analysis including Price, Volatility, Trend (ADX), Key Levels (Swings), RSI, EMA, and Funding Rate.
- **`get_order_book_analytics(coin)`**: Deep order book analysis including Imbalance, Liquidation Walls, and Premia.
- **`place_smart_order(coin, is_buy, size, size_type="usd", ...)`**: Flexible order placement with USD/Equity % sizing and optional TP/SL.
- **`get_account_info(type="perp")`**: Consolidated account info (Perp/Spot).
- **`get_exchange_meta(type="perp")`**: Consolidated exchange metadata.
- **`transfer(amount, destination, token="USDC")`**: Consolidated transfer tool.
- **`get_market_leaders()`**: Top Gainers/Vol.
- **`get_account_health()`**: Margin & Risk.
- **`close_position(...)`**: Close % of position.
- **`cancel_all_orders()`**: PANIC Cancel.
- **`close_all_positions()`**: PANIC Close.
- **`get_correlation_matrix()`**: 24h Price Correlation.
- **`get_volume_profile_24h()`**: Volume Profile Analysis.

> [!WARNING]
> This server has access to your trading account. Ensure your private key is kept secure and never shared.
