# AI Trading Agent

An autonomous trading agent for Hyperliquid using LangGraph and MCP.

## Quick Start

### 1. Install Dependencies

```bash
cd agent
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your keys
```

Required:
- `OPENROUTER_API_KEY` - Get from [openrouter.ai](https://openrouter.ai)
- `TELEGRAM_BOT_TOKEN` - Get from [@BotFather](https://t.me/BotFather)
- `TELEGRAM_CHAT_ID` - Get from [@userinfobot](https://t.me/userinfobot)

### 3. Start MCP Server

In a separate terminal:
```bash
cd deployment-test
python server.py --transport sse
```

### 4. Run Agent

```bash
# Using the main module
python -m agent.main

# Or using CLI
python -m ui.cli start
```

## CLI Commands

```bash
python -m ui.cli start          # Start the agent
python -m ui.cli status         # Show recent activity
python -m ui.cli trades         # Show trade history
python -m ui.cli positions      # Show open positions
python -m ui.cli config         # Show configuration
python -m ui.cli init           # Initialize database
```

## Architecture

Option B: Parallel Merge

```
[Supervisor] 
     ↓
[Parallel]
  ├── Analyst (Claude)
  └── Risk Manager (GPT-4o)
     ↓
[Merge Node]
     ↓
[Execute / Telegram Approval]
```

## Key Features

- **3-minute inference cycle**
- **Exit plans with invalidation conditions**
- **Telegram approval for large trades**
- **SQLite trade archival**
- **Rich CLI + Web dashboard**

## Risk Parameters

| Parameter | Default |
|-----------|---------|
| Max Position | 75% of portfolio |
| Max Drawdown | 50% |
| Leverage | Maximum |
| Auto-Approve | $100 |

## Files

```
agent/
├── main.py          # Entry point (3-min loop)
├── config.py        # Settings
├── llm_factory.py   # OpenRouter
├── graph.py         # LangGraph workflow
├── prompts.py       # Agent prompts
├── nodes/           # Analyst, Risk, Merge
├── approval/        # Telegram bot
└── db/              # SQLModel database
```

## ⚠️ Warning

This agent trades with **REAL MONEY** on **MAINNET**.
Ensure your risk parameters are configured correctly.
