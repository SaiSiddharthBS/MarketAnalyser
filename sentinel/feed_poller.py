"""
RSS Data Fetcher
"""
import feedparser
from config import RSS_FEEDS

def get_latest_headlines():
    headlines = []
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:
                headlines.append({
                    "headline": entry.get("title", ""),
                    "summary": entry.get("summary", ""),
                    "link": entry.link
                })
        except Exception as e:
            print(f"Error fetching feed {feed_url}: {e}")
            
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
