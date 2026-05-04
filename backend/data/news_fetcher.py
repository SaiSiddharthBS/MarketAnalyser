"""
MarketPulse — News & Sentiment Fetcher
Uses multiple sources with fallback for reliability.
"""
import requests
import xml.etree.ElementTree as ET
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime
import ssl
import traceback

# Fix Mac SSL issue
ssl._create_default_https_context = ssl._create_unverified_context

analyzer = SentimentIntensityAnalyzer()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"


def _fetch_google_news(query, max_results=10):
    """Fetch news from Google News RSS using requests (not feedparser)."""
    url = GOOGLE_NEWS_RSS.format(query=query.replace(" ", "+"))
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200 or not r.text.strip():
            return []
        root = ET.fromstring(r.text)
        articles = []
        items = root.findall(".//item")
        for item in items[:max_results]:
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            pub_date = item.findtext("pubDate", "")
            source_el = item.find("source")
            source = source_el.text if source_el is not None else "Unknown"
            
            sentiment = analyzer.polarity_scores(title)
            articles.append({
                "title": title,
                "link": link,
                "published": pub_date,
                "source": source,
                "sentiment_score": sentiment["compound"],
                "sentiment": "positive" if sentiment["compound"] > 0.05 else "negative" if sentiment["compound"] < -0.05 else "neutral",
            })
        return articles
    except Exception as e:
        print(f"Google News fetch error for '{query}': {e}")
        return []


def _fetch_yahoo_news(query="market", max_results=10):
    """Fallback: fetch news from Yahoo Finance search."""
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}&newsCount={max_results}&quotesCount=0"
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return []
        data = r.json()
        articles = []
        for item in data.get("news", [])[:max_results]:
            title = item.get("title", "")
            sentiment = analyzer.polarity_scores(title)
            articles.append({
                "title": title,
                "link": item.get("link", ""),
                "published": item.get("providerPublishTime", ""),
                "source": item.get("publisher", "Yahoo Finance"),
                "sentiment_score": sentiment["compound"],
                "sentiment": "positive" if sentiment["compound"] > 0.05 else "negative" if sentiment["compound"] < -0.05 else "neutral",
            })
        return articles
    except Exception as e:
        print(f"Yahoo News fetch error: {e}")
        return []


def fetch_news(query="Indian stock market", max_results=20):
    """Fetch news with Google News primary, Yahoo Finance fallback."""
    articles = _fetch_google_news(query, max_results)
    if not articles:
        # Fallback to Yahoo Finance news
        articles = _fetch_yahoo_news(query, max_results)
    return articles


def get_market_sentiment():
    """Get overall market sentiment from multiple queries."""
    queries = [
        "Nifty 50 today",
        "Indian stock market",
        "Sensex today",
        "RBI monetary policy",
        "FII investment India",
    ]
    all_scores = []
    all_articles = []

    for q in queries:
        articles = fetch_news(q, max_results=10)
        for a in articles:
            all_scores.append(a["sentiment_score"])
            all_articles.append(a)

    if not all_scores:
        return {"score": 0, "label": "Neutral", "positive_pct": 0, "negative_pct": 0, "articles": []}

    avg_score = sum(all_scores) / len(all_scores)
    positive = sum(1 for s in all_scores if s > 0.05)
    negative = sum(1 for s in all_scores if s < -0.05)
    total = len(all_scores)

    if avg_score > 0.1:
        label = "Bullish"
    elif avg_score > 0.03:
        label = "Mildly Bullish"
    elif avg_score < -0.1:
        label = "Bearish"
    elif avg_score < -0.03:
        label = "Mildly Bearish"
    else:
        label = "Neutral"

    # Remove duplicates by title
    seen = set()
    unique = []
    for a in all_articles:
        if a["title"] not in seen:
            seen.add(a["title"])
            unique.append(a)

    return {
        "score": round(avg_score, 4),
        "label": label,
        "positive_pct": round((positive / total) * 100, 1) if total else 0,
        "negative_pct": round((negative / total) * 100, 1) if total else 0,
        "articles": unique[:15],
    }


def get_market_news(max_results=20):
    """Get latest market news from multiple sources (deduplicated)."""
    queries = [
        "Indian stock market today",
        "Nifty Sensex today",
        "BSE NSE market news",
    ]
    all_articles = []
    seen_titles = set()

    for q in queries:
        articles = fetch_news(q, max_results=10)
        for a in articles:
            if a["title"] not in seen_titles:
                seen_titles.add(a["title"])
                all_articles.append(a)

    # Sort by absolute sentiment score (most opinionated first)
    all_articles.sort(key=lambda x: abs(x.get("sentiment_score", 0)), reverse=True)
    return all_articles[:max_results]


def get_stock_news(symbol):
    """Get news for a specific stock."""
    return fetch_news(f"{symbol} NSE stock", max_results=10)
