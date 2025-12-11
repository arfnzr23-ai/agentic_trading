"""
CLI Interface

Command-line interface for the AI Trading Agent.
"""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import asyncio

from agent.config import get_config
from agent.db import create_tables, get_session, TradeRepository, AgentLogRepository

app = typer.Typer(help="Hyperliquid AI Trading Agent CLI")
console = Console()


@app.command()
def start(
    mode: str = typer.Option("hybrid", help="Agent mode: autonomous, hybrid"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):
    """Start the trading agent."""
    console.print(Panel.fit(
        "[bold green]Starting Hyperliquid AI Trading Agent[/bold green]",
        border_style="green"
    ))
    
    cfg = get_config()
    
    # Display config
    table = Table(title="Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Mode", mode)
    table.add_row("MCP Server", cfg.mcp_server_url)
    table.add_row("Analyst Model", cfg.analyst_model)
    table.add_row("Risk Model", cfg.risk_model)
    table.add_row("Inference Interval", f"{cfg.inference_interval_seconds}s")
    table.add_row("Max Position", f"{cfg.risk.max_position_pct * 100}%")
    table.add_row("Auto-Approve Limit", f"${cfg.risk.auto_approve_usd}")
    
    console.print(table)
    console.print()
    
    # Start the main loop
    from agent.main import main_loop
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down...[/yellow]")


@app.command()
def status():
    """Show agent status and recent activity."""
    console.print(Panel.fit(
        "[bold cyan]Agent Status[/bold cyan]",
        border_style="cyan"
    ))
    
    with get_session() as session:
        # Recent logs
        logs = AgentLogRepository.get_recent(session, limit=10)
        
        table = Table(title="Recent Activity")
        table.add_column("Time", style="dim")
        table.add_column("Type", style="cyan")
        table.add_column("Output", style="white", max_width=50)
        
        for log in logs:
            table.add_row(
                log.timestamp.strftime("%H:%M:%S"),
                log.action_type,
                log.output[:50] + "..." if len(log.output) > 50 else log.output
            )
        
        console.print(table)


@app.command()
def trades(limit: int = typer.Option(20, help="Number of trades to show")):
    """Show recent trades."""
    console.print(Panel.fit(
        "[bold cyan]Trade History[/bold cyan]",
        border_style="cyan"
    ))
    
    with get_session() as session:
        recent_trades = TradeRepository.get_recent(session, limit=limit)
        
        if not recent_trades:
            console.print("[dim]No trades recorded yet.[/dim]")
            return
        
        table = Table(title=f"Last {limit} Trades")
        table.add_column("ID", style="dim")
        table.add_column("Coin", style="cyan")
        table.add_column("Dir", style="white")
        table.add_column("Size", style="white")
        table.add_column("PnL", style="green")
        table.add_column("Status", style="white")
        
        for trade in recent_trades:
            pnl_style = "green" if (trade.pnl_usd or 0) >= 0 else "red"
            pnl_str = f"${trade.pnl_usd:+.2f}" if trade.pnl_usd else "-"
            status = "OPEN" if trade.closed_at is None else trade.close_reason or "CLOSED"
            
            table.add_row(
                str(trade.id),
                trade.coin,
                trade.direction,
                f"${trade.size_usd:,.0f}",
                f"[{pnl_style}]{pnl_str}[/{pnl_style}]",
                status
            )
        
        console.print(table)


@app.command()
def positions():
    """Show open positions."""
    console.print(Panel.fit(
        "[bold cyan]Open Positions[/bold cyan]",
        border_style="cyan"
    ))
    
    with get_session() as session:
        open_trades = TradeRepository.get_open_trades(session)
        
        if not open_trades:
            console.print("[dim]No open positions.[/dim]")
            return
        
        table = Table()
        table.add_column("Coin", style="cyan")
        table.add_column("Direction", style="white")
        table.add_column("Entry", style="white")
        table.add_column("Size", style="white")
        table.add_column("Leverage", style="white")
        
        for trade in open_trades:
            table.add_row(
                trade.coin,
                trade.direction,
                f"${trade.entry_price:,.2f}",
                f"${trade.size_usd:,.0f}",
                f"{trade.leverage}x"
            )
        
        console.print(table)


@app.command()
def init():
    """Initialize the database."""
    console.print("[cyan]Initializing database...[/cyan]")
    create_tables()
    console.print("[green]OK - Database initialized![/green]")


@app.command()
def config():
    """Show current configuration."""
    cfg = get_config()
    
    table = Table(title="Current Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("OpenRouter API Key", "***" + cfg.openrouter_api_key[-4:] if cfg.openrouter_api_key else "Not set")
    table.add_row("Analyst Model", cfg.analyst_model)
    table.add_row("Risk Model", cfg.risk_model)
    table.add_row("MCP Server URL", cfg.mcp_server_url)
    table.add_row("Telegram Bot Token", "Set" if cfg.telegram_bot_token else "Not set")
    table.add_row("Database URL", cfg.database_url)
    table.add_row("Inference Interval", f"{cfg.inference_interval_seconds}s")
    table.add_row("Max Position %", f"{cfg.risk.max_position_pct * 100}%")
    table.add_row("Max Drawdown %", f"{cfg.risk.max_drawdown_pct * 100}%")
    table.add_row("Auto-Approve Limit", f"${cfg.risk.auto_approve_usd}")
    
    console.print(table)


def main():
    """CLI entry point."""
    app()


if __name__ == "__main__":
    main()
