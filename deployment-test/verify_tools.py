import server
import sys
import time

def test_tool(name, func, *args, **kwargs):
    print(f"Testing {name}...", end=" ")
    try:
        res = func(*args, **kwargs)
        if isinstance(res, str) and res.startswith("Error:"):
            print(f"FAIL: {res}")
            return False
        # Basic validation
        if isinstance(res, dict) and "error" in res:
             print(f"WARN: {res['error']}")
             return True # Not a crash, just API limit or missing data
        print("PASS")
        return True
    except Exception as e:
        print(f"CRASH: {e}")
        return False

def main():
    print("Initializing Server for Testing...")
    try:
        server.pm = server.PrecisionManager(server.info)
        server.pm.load()
    except Exception as e:
        print(f"Failed to initialize PrecisionManager: {e}")
    
    coin = "ETH"
    
    print("\n--- CONSOLIDATED ANALYTICS ---")
    test_tool("get_token_analytics", server.get_token_analytics, coin)
    test_tool("get_order_book_analytics", server.get_order_book_analytics, coin)
    test_tool("get_volume_profile_24h", server.get_volume_profile_24h, coin)
    test_tool("get_correlation_matrix", server.get_correlation_matrix, "BTC,ETH,SOL")
    
    print("\n--- ACCOUNT & RISK ---")
    test_tool("get_account_info", server.get_account_info)
    test_tool("get_account_health", server.get_account_health)
    test_tool("get_market_leaders", server.get_market_leaders)
    test_tool("get_position_risk", server.get_position_risk, coin)
    test_tool("get_max_trade_size", server.get_max_trade_size, coin)

    print("\n--- SMART TRADING (Dry Run / Check) ---")
    # We won't actually place orders here to avoid spending money, 
    # but we can check if the function exists and accepts args.
    print("place_smart_order exists:", hasattr(server, "place_smart_order"))

if __name__ == "__main__":
    main()
