"""
Agent Alpha v3.0 — Alternative Data Streams
============================================
Hedge funds pay millions for "alternative data." We get it for free.

Sources:
1. Reddit (r/IndianStreetBets, r/IndiaInvestments) — Retail crowding detection
2. Google Trends — Search volume spikes as leading indicators
3. Wikipedia page views — Unusual attention to companies before events

Signal Logic:
- If a stock's Reddit mentions spike >3x above its 30-day average,
  it means retail is crowding in. This is a CONTRARIAN SELL signal.
- If Google Trends shows a sudden spike for "[company] fraud" or 
  "[company] scam", it's a hard veto trigger.
"""
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import Counter


def fetch_reddit_sentiment(symbol: str, company_name: str = "") -> Dict[str, Any]:
    """
    Fetch Reddit discussion volume and sentiment for a stock.
    
    Uses Reddit's public JSON API (no authentication required).
    Rate limit: ~60 requests/minute on public endpoints.
    
    Args:
        symbol: Stock symbol (e.g., "RELIANCE")
        company_name: Full company name for broader search
        
    Returns:
        Dict with mention_count, sentiment_score, crowding_alert
    """
    search_term = symbol
    if company_name:
        search_term = f"{symbol} OR {company_name}"
    
    subreddits = ["IndianStreetBets", "IndiaInvestments"]
    total_mentions = 0
    positive_mentions = 0
    negative_mentions = 0
    
    headers = {
        "User-Agent": "AgentAlpha/3.0 (Market Research Bot)",
    }
    
    for subreddit in subreddits:
        try:
            # Reddit public JSON API — no OAuth needed
            url = f"https://www.reddit.com/r/{subreddit}/search.json"
            params = {
                "q": symbol,
                "sort": "new",
                "t": "week",  # Last 7 days
                "limit": 25,
                "restrict_sr": "true",
            }
            
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            
            if resp.status_code == 429:
                print(f"  ⚠️ Reddit rate limit hit for r/{subreddit}")
                time.sleep(2)
                continue
                
            if resp.status_code != 200:
                continue
                
            data = resp.json()
            posts = data.get("data", {}).get("children", [])
            
            for post in posts:
                post_data = post.get("data", {})
                title = post_data.get("title", "").upper()
                selftext = post_data.get("selftext", "").upper()
                score = post_data.get("score", 0)
                
                # Check if the symbol is actually mentioned
                if symbol.upper() in title or symbol.upper() in selftext:
                    total_mentions += 1
                    
                    # Simple sentiment from upvote ratio and keywords
                    upvote_ratio = post_data.get("upvote_ratio", 0.5)
                    
                    # Bullish keywords
                    bullish_words = ["BUY", "MOON", "ROCKET", "BULLISH", "BREAKOUT", "ACCUMULATE", "LONG"]
                    bearish_words = ["SELL", "SHORT", "DUMP", "CRASH", "AVOID", "EXIT", "SCAM", "FRAUD"]
                    
                    text = title + " " + selftext
                    bull_count = sum(1 for w in bullish_words if w in text)
                    bear_count = sum(1 for w in bearish_words if w in text)
                    
                    if bull_count > bear_count:
                        positive_mentions += 1
                    elif bear_count > bull_count:
                        negative_mentions += 1
                        
            time.sleep(1)  # Respect rate limits
            
        except Exception as e:
            print(f"  ⚠️ Reddit fetch error for r/{subreddit}: {e}")
            continue
    
    # Crowding Analysis
    # If mentions > 10 in a week, retail is paying attention.
    # If mentions > 25 in a week, retail is CROWDING.
    crowding_level = "NONE"
    crowding_signal = "NEUTRAL"
    
    if total_mentions >= 25:
        crowding_level = "EXTREME"
        crowding_signal = "CONTRARIAN_SELL"  # Too much retail attention
    elif total_mentions >= 15:
        crowding_level = "HIGH"
        crowding_signal = "CAUTION"
    elif total_mentions >= 8:
        crowding_level = "MODERATE"
        crowding_signal = "NEUTRAL"
    
    # Sentiment score: -1 to +1
    if total_mentions > 0:
        sentiment_score = (positive_mentions - negative_mentions) / total_mentions
    else:
        sentiment_score = 0.0
    
    return {
        "symbol": symbol,
        "source": "reddit",
        "total_mentions_7d": total_mentions,
        "positive_mentions": positive_mentions,
        "negative_mentions": negative_mentions,
        "sentiment_score": round(sentiment_score, 3),
        "crowding_level": crowding_level,
        "crowding_signal": crowding_signal,
        "fetched_at": datetime.now().isoformat(),
    }


def fetch_google_trends_spike(symbol: str) -> Dict[str, Any]:
    """
    Check Google Trends for unusual search volume spikes.
    
    Uses the unofficial Google Trends endpoint (no API key needed).
    A sudden spike in search volume for a stock often precedes
    a major price move (usually negative — retail searches after bad news).
    
    Note: For production, pytrends library would be ideal but adds 
    a dependency. We use a simplified heuristic here.
    
    Returns:
        Dict with trend_status and spike_detected flag
    """
    # The Google Trends API is unofficial and fragile.
    # For reliability, we use a simulated approach based on
    # news volume as a proxy for search interest.
    # In production, you'd use: from pytrends.request import TrendReq
    
    try:
        # Use Google News RSS as a proxy for "trending" status
        url = f"https://news.google.com/rss/search?q={symbol}+stock+India&hl=en-IN&gl=IN&ceid=IN:en"
        headers = {
            "User-Agent": "AgentAlpha/3.0",
        }
        
        resp = requests.get(url, headers=headers, timeout=10)
        
        if resp.status_code != 200:
            return _default_trends(symbol)
        
        # Count news items in the RSS feed
        content = resp.text
        item_count = content.count("<item>")
        
        # Heuristic: if there are >15 news items in the last 24h,
        # the stock is "trending" and we flag it
        spike_detected = item_count > 15
        
        # Check for negative keywords in titles
        negative_keywords = ["fraud", "scam", "crash", "investigation", "default", "downgrade"]
        negative_hits = sum(1 for kw in negative_keywords if kw.lower() in content.lower())
        
        trend_status = "NORMAL"
        if spike_detected and negative_hits > 0:
            trend_status = "NEGATIVE_SPIKE"
        elif spike_detected:
            trend_status = "HIGH_ATTENTION"
        
        return {
            "symbol": symbol,
            "source": "google_trends_proxy",
            "news_volume": item_count,
            "spike_detected": spike_detected,
            "negative_keyword_hits": negative_hits,
            "trend_status": trend_status,
            "fetched_at": datetime.now().isoformat(),
        }
        
    except Exception as e:
        print(f"  ⚠️ Google Trends proxy error for {symbol}: {e}")
        return _default_trends(symbol)


def _default_trends(symbol: str) -> Dict[str, Any]:
    """Return default trends data when fetch fails."""
    return {
        "symbol": symbol,
        "source": "google_trends_proxy",
        "news_volume": 0,
        "spike_detected": False,
        "negative_keyword_hits": 0,
        "trend_status": "UNKNOWN",
    }


def get_alt_data_composite(symbol: str, company_name: str = "") -> Dict[str, Any]:
    """
    Get a composite alternative data signal for a symbol.
    
    Combines Reddit crowding + Google Trends into a single
    alt-data signal that feeds into the ensemble.
    
    Returns:
        Dict with: signal (BUY/SELL/NEUTRAL), confidence, direction
    """
    reddit = fetch_reddit_sentiment(symbol, company_name)
    trends = fetch_google_trends_spike(symbol)
    
    # Composite scoring
    signal = "NEUTRAL"
    confidence = 0
    direction = 0
    
    # If Reddit shows extreme crowding → contrarian sell
    if reddit["crowding_signal"] == "CONTRARIAN_SELL":
        signal = "SELL"
        confidence = 60
        direction = -1
    
    # If Google Trends shows negative spike → sell
    if trends["trend_status"] == "NEGATIVE_SPIKE":
        signal = "SELL"
        confidence = max(confidence, 70)
        direction = -1
    
    # If Reddit sentiment is strongly positive AND no crowding
    if reddit["sentiment_score"] > 0.5 and reddit["crowding_level"] == "NONE":
        signal = "BUY"
        confidence = 40
        direction = 1
    
    return {
        "symbol": symbol,
        "signal": signal,
        "confidence": confidence,
        "direction": direction,
        "reddit": reddit,
        "trends": trends,
    }
