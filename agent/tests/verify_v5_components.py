"""
Verification Script for Context Optimization v5 Components

Tests:
1. chart_tools.py (TA-Lib integration)
2. news_fetcher.py (Graceful fallback)
3. data_fetcher.py (Smart Caching logic)
"""

import os
import sys
import asyncio
import time
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from agent.utils import chart_tools
from agent.services import news_fetcher
from agent.services import data_fetcher

def test_chart_tools():
    print("\n[TEST] 1. Chart Tools (TA-Lib)...")
    
    # Mock Candles (15 candles of data)
    # Rising price to test Uptrend/RSI
    candles = []
    base_price = 50000.0
    for i in range(50):
        base_price *= 1.001 # Slow rise
        candles.append({
            "o": base_price,
            "h": base_price + 100,
            "l": base_price - 100,
            "c": base_price + 50,
            "v": 1000 + (i * 10)
        })
        
    try:
        # Calculate Indicators
        indicators = chart_tools.calculate_indicators(candles, interval="1h")
        print(f"  > Indicators Calculated: {list(indicators.keys())}")
        print(f"  > RSI: {indicators['rsi']:.2f}")
        print(f"  > Regime: {indicators['regime']}")
        print(f"  > VWAP: {indicators['vwap']:.2f}")
        
        # Format String
        ctx_str = chart_tools.format_context_string("BTC", "1h", indicators, candles)
        print(f"  > Context String Preview:\n{ctx_str[:150]}...")
        
        print("  [PASS] Chart Tools")
    except Exception as e:
        print(f"  [FAIL] Chart Tools: {e}")
        import traceback
        traceback.print_exc()

def test_news_fallback():
    print("\n[TEST] 2. News Fetcher Fallback...")
    
    # Ensure Key is Unset/Empty for Test
    # (In real run, it might be set, but we want to simulate missing if user said so)
    # But user might have set it in .env, so we temporarily unset it for this test function scope if possible
    # Actually, we can just call it. If key is missing, it should handle it.
    
    # Force unset for verification
    original_key = news_fetcher.PERPLEXITY_API_KEY
    news_fetcher.PERPLEXITY_API_KEY = ""
    
    try:
        result = news_fetcher.fetch_macro_context()
        print(f"  > Result (No Key): {result}")
        
        if "API Key Missing" in result:
             print("  [PASS] Graceful Fallback verified.")
        else:
             print("  [FAIL] Did not return expected fallback message.")
             
    except Exception as e:
        print(f"  [FAIL] News Fetcher crashed: {e}")
    finally:
        news_fetcher.PERPLEXITY_API_KEY = original_key

async def test_caching():
    print("\n[TEST] 3. Smart Caching (Mocked)...")
    
    # Mock Tool
    class MockTool:
        def __init__(self, name):
            self.name = name
            self.calls = 0
        
        async def ainvoke(self, args):
            self.calls += 1
            if "interval" in args:
                # Return proper structure (List of Dicts)
                return [{"c": 100.0, "v": 1000}] * 5
            return "MockResult"
            
    mock_tools = [
        MockTool("get_market_context"),
        MockTool("get_candles"),
        MockTool("get_account_health")
    ]
    
    timestamps = {
        "current_ms": int(time.time() * 1000),
        "start_5m": 0, "start_1h": 0, "start_4h": 0, "start_1d": 0
    }
    
    # 1. First Fetch (Should populate cache)
    print("  > Run 1 (Cold Cache)...")
    res1 = await data_fetcher.fetch_analyst_data(mock_tools, "BTC", timestamps)
    print(f"    Fetched: {list(res1.keys())}")
    
    # Verify 1h was fetched
    candle_tool = mock_tools[1]
    calls_after_run1 = candle_tool.calls
    print(f"    Candle Tool Calls: {calls_after_run1}")
    
    # 2. Second Fetch (Should use cache for 1h/4h/1d)
    print("  > Run 2 (Warm Cache)...")
    res2 = await data_fetcher.fetch_analyst_data(mock_tools, "BTC", timestamps)
    
    calls_after_run2 = candle_tool.calls
    diff = calls_after_run2 - calls_after_run1
    # Expect 1 call (only 5m should be fetched)
    print(f"    Candle Tool Calls Added: {diff}")
    
    if diff == 1:
        print("  [PASS] Caching logic working (Only 5m fetched).")
    else:
        print(f"  [FAIL] Caching logic failed. Expected 1 call, got {diff}.")
        
    # 3. Volatility Trigger
    print("  > Testing Volatility Valve...")
    # Trigger a volatility check manually if possible or simulate price move
    # We'll simulate by manipulating the _LAST_PRICE_CHECK logic indirectly or calling the internal func
    data_fetcher._LAST_PRICE_CHECK = {"price": 100.0, "time": timestamps["current_ms"] - 120000} # 2 mins ago
    
    # Trigger check with higher price
    data_fetcher._check_volatility(105.0, timestamps["current_ms"]) # 5% move
    
    if len(data_fetcher._MARKET_CACHE) == 0:
        print("  [PASS] Cache cleared on volatility.")
    else:
        print(f"  [FAIL] Cache not cleared. Items: {len(data_fetcher._MARKET_CACHE)}")


if __name__ == "__main__":
    test_chart_tools()
    test_news_fallback()
    asyncio.run(test_caching())
