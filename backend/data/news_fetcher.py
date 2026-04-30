"""
MarketPulse — News & Sentiment Fetcher
Uses Google News RSS + VADER for free sentiment analysis.
"""
import feedparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime

analyzer = SentimentIntensityAnalyzer()

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"


def fetch_news(query="Indian stock market", max_results=20):
    """Fetch news from Google News RSS."""
    url = GOOGLE_NEWS_RSS.format(query=query.replace(" ", "+"))
    try:
        feed = feedparser.parse(url)
        articles = []
        for entry in feed.entries[:max_results]:
            title = entry.get("title", "")
            sentiment = analyzer.polarity_scores(title)
            articles.append({
                "title": title,
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
                "source": entry.get("source", {}).get("title", "Unknown"),
                "sentiment_score": sentiment["compound"],
                "sentiment": "positive" if sentiment["compound"] > 0.05 else "negative" if sentiment["compound"] < -0.05 else "neutral",
            })
        return articles
    except Exception as e:
        print(f"Error fetching news: {e}")
        return []


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
        return {"score": 0, "label": "neutral", "articles": []}

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


def get_stock_news(symbol):
    """Get news for a specific stock."""
    return fetch_news(f"{symbol} NSE stock", max_results=10)
