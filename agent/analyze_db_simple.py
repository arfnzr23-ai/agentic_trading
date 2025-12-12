import sqlite3
import json
import os

DB_PATH = "agent(1).db"

def analyze_losses():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Query logs
    query = """
    SELECT 
        timestamp,
        analyst_signal,
        final_action,
        final_reasoning
    FROM inference_logs 
    WHERE final_action IN ('EXECUTED', 'CUT_LOSS', 'CLOSE') 
    ORDER BY timestamp DESC 
    LIMIT 10
    """
    
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        
        print(f"ANALYSIS OF LAST {len(rows)} EXECUTED TRADES")
        print("="*60)
        
        for row in rows:
            ts, sig_json, action, reasoning = row
            signal = json.loads(sig_json) if sig_json else {}
            sig_type = signal.get("signal", "N/A")
            conf = signal.get("confidence", 0)
            
            print(f"[{ts}] {action} | Sig: {sig_type} ({conf}%)")
            print(f"Reasoning: {reasoning}")
            print("-" * 40)
            
    except Exception as e:
        print(f"Error querying DB: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    analyze_losses()
