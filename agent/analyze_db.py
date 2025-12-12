import sqlite3
import pandas as pd
from tabulate import tabulate
import json
import os

DB_PATH = "agent(1).db"

def analyze_losses():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    
    # Query logs
    query = """
    SELECT 
        timestamp,
        analyst_signal,
        risk_decision,
        final_action,
        final_reasoning,
        risk_reasoning
    FROM inference_logs 
    ORDER BY timestamp DESC 
    LIMIT 20
    """
    
    try:
        df = pd.read_sql_query(query, conn)
        
        print(f"ANALYSIS OF LAST {len(df)} INFERENCE CYCLES")
        print("="*60)
        
        for index, row in df.iterrows():
            signal = json.loads(row['analyst_signal']) if row['analyst_signal'] else {}
            risk = json.loads(row['risk_decision']) if row['risk_decision'] else {}
            
            action = row['final_action']
            ts = row['timestamp']
            
            sig_str = f"{signal.get('signal')} ({signal.get('confidence')}%)"
            risk_str = f"{risk.get('decision') or risk.get('action')}"
            
            print(f"[{ts}] Action: {action} | Sig: {sig_str} | Risk: {risk_str}")
            print(f"   > Reasoning: {row['final_reasoning']}")
            print("-" * 40)
            
    except Exception as e:
        print(f"Error querying DB: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    analyze_losses()
