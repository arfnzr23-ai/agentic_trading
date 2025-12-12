"""
Data Fetcher Module

Parallel tool execution using asyncio.gather() for faster data collection.
"""

import asyncio
import time
from typing import Any


# Global Cache
# Structure: {key: {"data": data, "timestamp": ms}}
_MARKET_CACHE = {}
_LAST_PRICE_CHECK = {"price": 0.0, "time": 0}

async def fetch_analyst_data(tools: list, coin: str, timestamps: dict, wallet_address: str) -> dict:
    """
    Fetch all data for analyst using Server-Side Aggregator (Phase 6).
    """
    tool_map = {t.name: t for t in tools}
    
    # 1. Single Aggregator Call
    print(f"[DataFetcher] Fetching full context for {coin}...")
    start = time.time()
    
    # Call the new "Mega-Tool"
    raw_data = await _call_tool(
        tool_map.get("get_agent_full_context"), 
        {"coin": coin, "address": wallet_address}
    )
    
    elapsed = (time.time() - start) * 1000
    print(f"[DataFetcher] Aggregated Fetch completed in {elapsed:.0f}ms")
    
    if isinstance(raw_data, str):
        print(f"[DataFetcher] DEBUG RAW DATA TYPE: {type(raw_data)}")
        print(f"[DataFetcher] DEBUG RAW DATA (First 500 chars): {raw_data[:500]}")
        if "Error" in raw_data:
            print(f"[DataFetcher] Critical Error: {raw_data}")
            return {}
        # Try one last parse if it's a valid stringified dict that _call_tool missed?
        # But for now let's just see what it is.


    # 2. Unpack & Normalize Results
    final_results = {}
    
    if isinstance(raw_data, dict):
        # Happy Path
        final_results["market_context"] = raw_data.get("market_context", {})
        final_results["candles_1m"] = raw_data.get("candles_1m", [])
        final_results["candles_5m"] = raw_data.get("candles_5m", [])
        final_results["candles_1h"] = raw_data.get("candles_1h", [])
        final_results["candles_4h"] = raw_data.get("candles_4h", [])
        final_results["candles_1d"] = raw_data.get("candles_1d", [])
        final_results["user_fills"] = raw_data.get("user_fills", [])
        final_results["open_orders"] = raw_data.get("open_orders", []) # Fix missing field
        
        user_state = raw_data.get("user_state", {})
    else:
        # Error Path (raw_data is str)
        print(f"[DataFetcher] 🛑 AGGREGATOR ERROR: Expected dict, got {type(raw_data)}. Value: {str(raw_data)[:200]}")
        final_results["market_context"] = {}
        final_results["candles_1m"] = []
        final_results["candles_5m"] = []
        final_results["candles_1h"] = []
        final_results["candles_4h"] = []
        final_results["candles_1d"] = []
        final_results["user_fills"] = []
        final_results["open_orders"] = []
        user_state = {}

    # Map 'user_state' (raw HL response) to 'account_health' (Agent format)
    # If the server returned 'account_health' directly in future, we'd use that.
    # Currently server returns 'user_state'.
    if user_state:
        margin_summary = user_state.get("marginSummary", {})
        final_results["account_health"] = {
            "equity": float(margin_summary.get("accountValue", 0)),
            "margin_used": float(margin_summary.get("totalMarginUsed", 0)),
            "margin_available": float(margin_summary.get("totalNtlPos", 0)), # Approx
            # Add other fields if needed by nodes
        }
        # Also expose raw state for risk node if needed
        final_results["account_state"] = user_state
        final_results["open_orders"] = raw_data.get("open_orders", [])
    else:
        final_results["account_health"] = "Error: No user state"

    # 3. Volatility Check (Safety Valve)
    # Use 1m candle for fastest check now
    try:
        c1m = final_results.get("candles_1m")
        current_ms = timestamps["current_ms"]
        current_price = 0.0
        
        if c1m and isinstance(c1m, list) and len(c1m) > 0:
            last = c1m[-1]
            # Handle potential MCP TextContent wrapper if server didn't clean it (server sent raw)
            # But wait, server sent raw list from HL SDK -> HL SDK returns list of dicts.
            # However, MCP transmission might stringify or wrap?
            # FastMCP generally serializes JSON. So it should be dicts.
            if isinstance(last, dict):
                 current_price = float(last.get("c", 0))
        
        if current_price > 0:
            _check_volatility(current_price, current_ms)
            
    except Exception as e:
        print(f"[DataFetcher] Volatility check warning: {e}")

    return final_results


def _check_volatility(current_price: float, current_ms: int):
    """
    If price moves > 1% in 1 minute, invalidate all caches.
    """
    global _MARKET_CACHE, _LAST_PRICE_CHECK
    
    last_price = _LAST_PRICE_CHECK["price"]
    last_time = _LAST_PRICE_CHECK["time"]
    
    # Initialize if empty
    if last_price == 0:
        _LAST_PRICE_CHECK = {"price": current_price, "time": current_ms}
        return

    # Check time delta (approx 1 min window)
    if current_ms - last_time > 60 * 1000:
        # Calculate move
        pct_change = abs((current_price - last_price) / last_price) * 100
        
        if pct_change > 1.0:
            print(f"[DataFetcher] ⚠️ High Volatility ({pct_change:.2f}%). Invalidating Cache.")
            _MARKET_CACHE.clear()
        
        # Update checkpoint
        _LAST_PRICE_CHECK = {"price": current_price, "time": current_ms}



async def _call_tool(tool, args: dict) -> Any:
    """Call a single tool safely."""
    if tool is None:
        return "Error: Tool not found"
    
    try:
        result = await tool.ainvoke(args)
        
        # Unpack standard MCP/LangChain ToolMessage result
        if isinstance(result, list):
            # Check for TextContent objects (common in FastMCP/LangChain)
            content_list = []
            for item in result:
                if hasattr(item, 'text'):
                    content_list.append(item.text)
                elif isinstance(item, dict) and "text" in item:
                    content_list.append(item["text"])
                elif isinstance(item, str):
                    content_list.append(item)
            
            full_text = "".join(content_list)
            
            # Try to parse as JSON if it looks like it
            if full_text.strip().startswith("{") or full_text.strip().startswith("["):
                try:
                    import json
                    return json.loads(full_text)
                except:
                    return full_text
            return full_text
            
        return result
    except Exception as e:
        return f"Error: {str(e)}"


def calculate_timestamps() -> dict:
    """Calculate standard timestamp ranges for candle fetching."""
    current_ms = int(time.time() * 1000)
    
    return {
        "current_ms": current_ms,
        "start_1m": current_ms - (120 * 60 * 1000),         # Last 2 hours of 1m candles
        "start_5m": current_ms - (50 * 5 * 60 * 1000),      # Last 50 5-min candles (~4h)
        "start_1h": current_ms - (48 * 60 * 60 * 1000),    # Last 48 1-hour candles (2 days)
        "start_4h": current_ms - (50 * 4 * 60 * 60 * 1000), # Last 50 4-hour candles (~8 days)
        "start_1d": current_ms - (30 * 24 * 60 * 60 * 1000) # Last 30 daily candles (~1 month)
    }


def summarize_candles(candles_json: str, max_candles: int = 10) -> str:
    """
    Compress candle data for LLM consumption.
    Shows summary stats AND recent candle patterns for structure analysis.
    """
    import json
    
    try:
        if isinstance(candles_json, str):
            if candles_json.startswith('['):
                candles = json.loads(candles_json)
            elif candles_json.startswith('Error'):
                return f"FETCH ERROR: {candles_json}"
            else:
                return "No candle data available."
        else:
            candles = candles_json if candles_json else []
            
        if not candles:
            return "No candles returned from API."
            
        # Parse candles (handle both string and dict formats)
        parsed = []
            
        for c in candles[-max_candles:]:
            # Handle MCP/LangChain TextContent objects (dict with 'text' field)
            if isinstance(c, dict) and "text" in c and isinstance(c.get("text"), str):
                try:
                    import json
                    c = json.loads(c["text"])
                except Exception:
                    continue
            # Handle stringified JSON
            elif isinstance(c, str):
                try:
                    import json
                    c = json.loads(c)
                except Exception:
                    continue
            
            # Extract data
            try:
                parsed.append({
                    "o": float(c.get("o", 0)),
                    "h": float(c.get("h", 0)),
                    "l": float(c.get("l", 0)),
                    "c": float(c.get("c", 0))
                })
            except Exception:
                continue
        
        if not parsed:
            return "Could not parse candle data."
            
        # Calculate summary stats
        opens = [c["o"] for c in parsed]
        highs = [c["h"] for c in parsed]
        lows = [c["l"] for c in parsed]
        closes = [c["c"] for c in parsed]
        
        current = closes[-1]
        first_close = closes[0]
        trend_pct = ((current / first_close) - 1) * 100 if first_close else 0
        volatility = ((max(highs) - min(lows)) / current) * 100 if current else 0
        
        # Recent 5 candle pattern for structure
        recent_5 = parsed[-5:] if len(parsed) >= 5 else parsed
        pattern = []
        for i, c in enumerate(recent_5):
            body = c["c"] - c["o"]
            candle_type = "GREEN" if body > 0 else "RED" if body < 0 else "DOJI"
            pattern.append(f"{candle_type}(${c['c']:.0f})")
        
        # Structure analysis: Compare swing points (not just consecutive candles)
        # A swing high is a candle with lower highs on both sides
        # A swing low is a candle with higher lows on both sides
        
        recent_highs = highs[-10:] if len(highs) >= 10 else highs
        recent_lows = lows[-10:] if len(lows) >= 10 else lows
        
        # Simple structure: compare first half avg vs second half avg
        mid = len(recent_highs) // 2
        first_half_high = sum(recent_highs[:mid]) / max(mid, 1)
        second_half_high = sum(recent_highs[mid:]) / max(len(recent_highs) - mid, 1)
        first_half_low = sum(recent_lows[:mid]) / max(mid, 1)
        second_half_low = sum(recent_lows[mid:]) / max(len(recent_lows) - mid, 1)
        
        # Determine structure based on how highs and lows are moving
        higher_highs = second_half_high > first_half_high
        higher_lows = second_half_low > first_half_low
        lower_highs = second_half_high < first_half_high
        lower_lows = second_half_low < first_half_low
        
        if higher_highs and higher_lows:
            structure = "BULLISH (HH+HL)"
        elif lower_highs and lower_lows:
            structure = "BEARISH (LH+LL)"
        elif higher_lows and not lower_highs:
            structure = "BULLISH BIAS (HL forming)"
        elif lower_highs and not higher_lows:
            structure = "BEARISH BIAS (LH forming)"
        else:
            structure = "RANGING (no clear trend)"
        
        # Key levels
        swing_high = max(highs[-5:]) if len(highs) >= 5 else max(highs)
        swing_low = min(lows[-5:]) if len(lows) >= 5 else min(lows)
        
        return f"""Range: ${min(lows):.2f} - ${max(highs):.2f}
Current: ${current:.2f}
Trend: {'UP' if trend_pct > 0 else 'DOWN'} ({trend_pct:+.2f}%)
Volatility: {volatility:.2f}%
Structure: {structure}
Key Levels: Support ${swing_low:.2f} | Resistance ${swing_high:.2f}
Recent 5: {' -> '.join(pattern)}"""
        
    except Exception as e:
        return f"Candle parse error: {e}"
