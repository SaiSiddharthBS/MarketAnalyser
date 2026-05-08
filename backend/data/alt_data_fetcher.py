"""
Agent Alpha v3.0 — Alternative Data Engine
==========================================
Extracts retail sentiment and crowding metrics using completely free streams.

1. Reddit Scraping (r/IndianStreetBets) - Detects retail euphoria.
2. Google Trends - Detects search volume spikes for tickers.
"""
import requests
import time
from typing import Dict, Any, List
from datetime import datetime, timedelta

# Avoid rate limits by using a custom user agent
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_reddit_sentiment(subreddit: str = "IndianStreetBets", limit: int = 50) -> Dict[str, Any]:
    """
    Fetch hot posts from a subreddit to gauge retail sentiment and ticker mentions.
    Returns a sentiment score and top mentioned tickers.
    """
    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            return {"error": f"HTTP {response.status_code}"}
            
        data = response.json()
        posts = data.get("data", {}).get("children", [])
        
        text_corpus = ""
        upvotes = 0
        
        for post in posts:
            post_data = post.get("data", {})
            title = post_data.get("title", "")
            selftext = post_data.get("selftext", "")
            score = post_data.get("score", 0)
            
            text_corpus += f" {title} {selftext} "
            upvotes += score
            
        # Basic keyword matching for retail euphoria/panic
        euphoria_keywords = ["moon", "rocket", "yolo", "call", "buy", "bull", "rally", "breakout"]
        panic_keywords = ["crash", "put", "sell", "bear", "loss", "blood", "red", "dip"]
        
        text_lower = text_corpus.lower()
        euphoria_count = sum(text_lower.count(k) for k in euphoria_keywords)
        panic_count = sum(text_lower.count(k) for k in panic_keywords)
        
        total_signals = euphoria_count + panic_count
        if total_signals == 0:
            sentiment_ratio = 0.5
        else:
            sentiment_ratio = euphoria_count / total_signals
            
        return {
            "retail_sentiment_ratio": round(sentiment_ratio, 2), # > 0.7 = Extreme Euphoria (Danger)
            "euphoria_mentions": euphoria_count,
            "panic_mentions": panic_count,
            "total_upvotes_analyzed": upvotes,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Reddit scrape failed: {e}")
        return {"error": str(e)}


def fetch_google_trends_spike(symbol: str) -> Dict[str, Any]:
    """
    Detects if a ticker is experiencing a sudden spike in retail search volume.
    Requires 'pytrends' library.
    """
    try:
        from pytrends.request import TrendReq
        
        # Connect to Google
        pytrends = TrendReq(hl='en-IN', tz=330, timeout=(10,25))
        
        # Clean symbol (e.g., RELIANCE.NS -> RELIANCE Share)
        clean_term = symbol.replace('.NS', '').replace('.BO', '') + " share"
        
        pytrends.build_payload([clean_term], cat=0, timeframe='now 7-d', geo='IN', gprop='')
        df = pytrends.interest_over_time()
        
        if df.empty:
            return {"spike_detected": False, "momentum": 0}
            
        # Analyze last 7 days of search volume
        recent_volume = df[clean_term].iloc[-24:].mean() # Last 24 hours
        past_volume = df[clean_term].iloc[:-24].mean()   # Previous 6 days
        
        if past_volume == 0:
            momentum = 0
        else:
            momentum = (recent_volume - past_volume) / past_volume
            
        return {
            "symbol": symbol,
            "search_momentum_pct": round(momentum * 100, 2),
            "spike_detected": momentum > 1.5, # > 150% increase in search volume
            "timestamp": datetime.now().isoformat()
        }
        
    except ImportError:
        print("⚠️ pytrends not installed. Run: pip install pytrends")
        return {"error": "pytrends not installed"}
    except Exception as e:
        print(f"❌ Google Trends fetch failed: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    print("Testing Alt-Data Fetcher...")
    print(fetch_reddit_sentiment())
