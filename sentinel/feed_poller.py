"""
RSS Data Fetcher
"""
import feedparser
from config import RSS_FEEDS

import requests

def get_latest_headlines():
    headlines = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    for feed_url in RSS_FEEDS:
        try:
            res = requests.get(feed_url, headers=headers, timeout=10)
            if res.status_code == 200:
                feed = feedparser.parse(res.text)
                for entry in feed.entries[:10]:
                    headlines.append({
                        "headline": entry.get("title", ""),
                        "summary": entry.get("summary", ""),
                        "link": entry.link
                    })
            # Silently ignore non-200 status codes to keep console clean
        except Exception:
            # Silently ignore connection timeouts/errors
            pass
            
    # Add NSE/BSE data
    headlines.extend(get_nse_announcements())
    headlines.extend(get_bse_announcements())
    return headlines

def get_nse_announcements():
    """Fetch corporate announcements from NSE."""
    # Placeholder for NSE API Integration
    return []
    
def get_bse_announcements():
    """Fetch corporate announcements from BSE."""
    # Placeholder for BSE API Integration
    return []
