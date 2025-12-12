"""
News Fetcher Module (Perplexity Integration)

Fetches macro-economic context using Perplexity Sonar API.
Triggered daily or on high volatility events.
"""

import os
import requests
import time
from agent.db.async_logger import async_logger

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

def fetch_macro_context(query: str = "Summarize top 3 crypto market drivers today") -> str:
    """
    Fetch macro context from Perplexity.
    
    Args:
        query: prompt for the reasoning engine
        
    Returns:
        Structured string of news context
    """
    if not PERPLEXITY_API_KEY:
        print("[News] PERPLEXITY_API_KEY not found. Skipping news fetch.")
        return "Macro Context: N/A (API Key Missing)"
        
    url = "https://api.perplexity.ai/chat/completions"
    
    payload = {
        "model": "sonar-reasoning", # or sonar-pro
        "messages": [
            {
                "role": "system",
                "content": "You are a senior crypto market analyst. Provide a concise, bulleted summary of the requested topic. Focus on facts, regulatory news, and major hacks/macro events. No generic advice."
            },
            {
                "role": "user",
                "content": query
            }
        ],
        "temperature": 0.2
    }
    
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        start = time.time()
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        
        elapsed = (time.time() - start) * 1000
        print(f"[News] Perplexity fetch successful in {elapsed:.0f}ms")
        
        async_logger.log(
            action_type="NEWS_FETCH",
            node_name="news_fetcher",
            output=content[:500],
            reasoning=f"Query: {query}"
        )
        
        return f"### Macro Context (Source: Perplexity)\n{content}"
        
    except Exception as e:
        print(f"[News] Fetch Error: {e}")
        return f"Macro Context: Error fetching news ({str(e)})"
