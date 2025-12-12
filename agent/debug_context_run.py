"""
Debug Script: Context Injection Preview

This script connects to the local MCP server (or mocks it), fetches data,
and constructs the exact context string that is sent to the Analyst LLM.
Use this to verify what the agent "sees".
"""

import asyncio
import os
import sys
import time
from langchain_mcp_adapters.client import MultiServerMCPClient
from agent.services import data_fetcher
from agent.utils import chart_tools

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

async def main():
    print("="*60)
    print("CONTEXT INJECTION PREVIEW")
    print("="*60)
    
    # 1. Setup Client
    print("[1/4] Connecting to MCP Server...")
    
    mcp_config = {
        "hyperliquid": {
            "url": "http://localhost:8000/sse",
            "transport": "sse"
        }
    }
    
    try:
        # Initialize with config
        client = MultiServerMCPClient(mcp_config)
        print("  > Client Initialized (Connecting via get_tools)...")
        
        # 2. Get Tools (triggers connection)
        tools = await client.get_tools()
        print(f"  > Connected! {len(tools)} tools available: {[t.name for t in tools]}")
    except Exception as e:
        print(f"  > Could not connect to MCP: {e}")
        print("  > Switching to MOCK MODE for demonstration.")
        return
    
    # 3. Fetch Data (Real)
    print("\n[2/4] Fetching Data (data_fetcher.py)...")
    # Load Env
    from dotenv import load_dotenv
    load_dotenv()
    wallet_address = os.getenv("AG_WL") or os.getenv("HL_WL")
    
    target_coin = "BTC"
    timestamps = data_fetcher.calculate_timestamps()
    
    start_time = time.time()
    data = await data_fetcher.fetch_analyst_data(tools, target_coin, timestamps, wallet_address)
    duration = (time.time() - start_time) * 1000
    print(f"  > Fetch Complete in {duration:.0f}ms")
    print(f"  > Keys: {list(data.keys())}")
    
    # 4. Construct Context (Replicating Analyst v2 Logic)
    print("\n[3/4] Processing Data & Formatting Prompt...")
    
    # Clean & Parse
    def _clean(raw_data) -> list:
        try:
            import json as _json
            if isinstance(raw_data, list):
                # Check if it's a list of TextContent objects
                cleaned = []
                for c in raw_data:
                    if isinstance(c, dict):
                         if "text" in c:
                             try: cleaned.append(_json.loads(c["text"]))
                             except: continue
                         else:
                             cleaned.append(c)
                return cleaned
            elif isinstance(raw_data, str):
                if raw_data.startswith('['):
                    return _json.loads(raw_data)
        except Exception:
             return []
        return []
    
    print("  > Parsing Candles...")
        
    c5m = _clean(data.get("candles_5m", []))
    c1m = _clean(data.get("candles_1m", [])) # NEW
    c1h = _clean(data.get("candles_1h", []))
    c4h = _clean(data.get("candles_4h", []))
    c1d = _clean(data.get("candles_1d", []))
    
    # Chart Tools
    ind_5m = chart_tools.calculate_indicators(c5m, "5m")
    ind_1m = chart_tools.calculate_indicators(c1m, "1m") # NEW
    ind_1h = chart_tools.calculate_indicators(c1h, "1h")
    ind_4h = chart_tools.calculate_indicators(c4h, "4h")
    ind_1d = chart_tools.calculate_indicators(c1d, "1d")
    
    str_5m = chart_tools.format_context_string(target_coin, "5m", ind_5m, c5m)
    str_1m = chart_tools.format_context_string(target_coin, "1m", ind_1m, c1m) # NEW
    str_1h = chart_tools.format_context_string(target_coin, "1h", ind_1h, c1h)
    str_4h = chart_tools.format_context_string(target_coin, "4h", ind_4h, c4h)
    str_1d = chart_tools.format_context_string(target_coin, "1d", ind_1d, c1d)
    
    # User Fills
    user_fills = data.get("user_fills", [])
    fills_str = "No recent trades."
    
    try:
        user_fills_clean = _clean(user_fills)
        relevant_fills = [f for f in user_fills_clean if isinstance(f, dict) and f.get("coin") == target_coin]
        
        if relevant_fills:
            print(f"DEBUG: Raw Fill Sample: {relevant_fills[0]}")
            relevant_fills.sort(key=lambda x: x.get("time", 0), reverse=True)
            
            fill_lines = []
            for f in relevant_fills[:5]:
                side = "BUY" if f.get("side") == "B" else "SELL"
                px = float(f.get("px", 0))
                sz = float(f.get("sz", 0))
                ts = f.get("time", 0)
                
                try:
                    dt = (time.time() * 1000 - ts) / 1000
                    if dt < 3600: t_str = f"{dt/60:.0f}m ago"
                    elif dt < 86400: t_str = f"{dt/3600:.1f}h ago"
                    else: t_str = f"{dt/86400:.1f}d ago"
                except: t_str = "Unknown time"
                
                # PnL & Type
                pnl = float(f.get("closedPnl", 0))
                pnl_str = f" | PnL: ${pnl:+.2f}" if pnl != 0 else ""
                
                # Order Type (heuristic based on 'crossing')
                # details might vary, but usually crossing=True means taker (Market)
                is_taker = f.get("crossing", True) 
                type_str = "Market" if is_taker else "Limit"
                
                fill_lines.append(f"- {side} ${px:,.2f} ({sz}) | {type_str}{pnl_str} | {t_str}")
            
            fills_str = "\n".join(fill_lines)
    except Exception as e:
        fills_str = f"Error parsing fills: {e}"
    
    # Account
    account = data.get("account_health", "N/A")
    
    # 5. Output
    print("\n" + "="*60)
    print("FINAL INJECTED PROMPT (Snippet)")
    print("="*60)
    
    prompt_preview = f"""
## MULTI-TIMEFRAME STRUCTURE (Macro -> Micro)

### 1D (Daily Trend)
{str_1d}

### 4H (Swing Trend)
{str_4h}

### 1H (Intraday Trend)
{str_1h}

### 5M (Entry Timing)
### 5M (Entry Timing)
{str_5m}

### 1M (Scalp Momentum)
{str_1m}

### RECENT TRADING ACTIVITY
{fills_str}

### Account
{account}
"""
    print(prompt_preview)
    print("="*60)
    
    print("="*60)
    # End

if __name__ == "__main__":
    asyncio.run(main())
