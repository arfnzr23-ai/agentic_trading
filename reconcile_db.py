
import asyncio
import os
import sys
from sqlmodel import select
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath("."))

from agent.db import get_session, Trade, ExitPlan
from hyperliquid.info import Info
from hyperliquid.utils import constants
from dotenv import load_dotenv

from pathlib import Path
agent_dir = Path(r"c:\hyperliquid-mcp-agent\agent")
env_path = agent_dir / ".env"
print(f"Loading env from: {env_path}")
load_dotenv(env_path)
print(f"HL_WL Loaded: {os.getenv('HL_WL')}")

def reconcile():
    print("--- Starting DB Reconciliation ---")
    
    # 1. Get Actual Exchange State
    address = os.getenv("HL_WL")
    if not address:
        print("Error: HL_WL not set in env")
        return

    try:
        url = constants.MAINNET_API_URL
        info = Info(url, skip_ws=True)
        user_state = info.user_state(address)
        
        real_positions = {}
        for p in user_state.get("assetPositions", []):
            pos = p.get("position", {})
            coin = pos.get("coin")
            szi = float(pos.get("szi", 0))
            if szi != 0:
                real_positions[coin] = szi
                
        print(f"Real Positions on Exchange: {real_positions}")
        
    except Exception as e:
        print(f"Failed to fetch exchange state: {e}")
        return

    # 2. Get DB State
    with get_session() as session:
        statement = select(Trade).where(Trade.closed_at == None)
        db_trades = session.exec(statement).all()
        
        print(f"Open Trades in DB: {[t.coin for t in db_trades]}")
        
        # 3. Reconcile
        for trade in db_trades:
            if trade.coin not in real_positions:
                print(f"Mismatch found! Trade {trade.id} ({trade.coin}) exists in DB but not on Exchange.")
                print(f"-> Closing Ghost Trade {trade.id}...")
                
                # Mark as closed
                trade.closed_at = datetime.utcnow()
                trade.close_reason = "RECONCILIATION_FIX"
                trade.pnl_usd = 0 # Assume breakeven/loss for ghost trades
                
                # Close associated Exit Plan
                if trade.exit_plan:
                    trade.exit_plan.status = "CLOSED"
                    trade.exit_plan.triggered_reason = "RECONCILIATION_FIX"
                    session.add(trade.exit_plan)
                
                session.add(trade)
                
            else:
                print(f"Trade {trade.id} ({trade.coin}) matches verified position.")
                
        session.commit()
        print("--- Reconciliation Complete ---")

if __name__ == "__main__":
    reconcile()
