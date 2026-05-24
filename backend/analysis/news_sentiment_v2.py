"""
Agent Alpha — News Sentiment Engine V2
======================================
Fetches recent news headlines for a stock and uses financial NLP heuristics
to score the sentiment (Bullish/Bearish/Neutral).
"""

import yfinance as yf
import logging
import re
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Very basic financial sentiment lexicons (offline)
BULLISH_WORDS = {
    "surge", "surges", "jump", "jumps", "rally", "rallies", "gain", "gains", "up", "higher",
    "beat", "beats", "upgrade", "upgrades", "buy", "buys", "positive", "strong", "growth",
    "profit", "profits", "dividend", "dividends", "record", "soars", "soar", "breakout",
    "outperform", "outperforms", "bullish"
}

BEARISH_WORDS = {
    "plunge", "plunges", "drop", "drops", "fall", "falls", "down", "lower", "miss", "misses",
    "downgrade", "downgrades", "sell", "sells", "negative", "weak", "loss", "losses", "cut",
    "cuts", "slump", "slumps", "crash", "crashes", "underperform", "underperforms", "bearish",
    "probe", "investigate", "fraud", "scam", "lawsuit", "penalty", "default"
}

def analyze_headline(text: str) -> float:
    """Returns a score between -1.0 and 1.0 based on lexical matching."""
    if not text:
        return 0.0
        
    words = set(re.findall(r'\b[a-z]+\b', text.lower()))
    
    bull_count = len(words.intersection(BULLISH_WORDS))
    bear_count = len(words.intersection(BEARISH_WORDS))
    
    total = bull_count + bear_count
    if total == 0:
        return 0.0
        
    # Simple ratio mapping to -1 to +1
    return (bull_count - bear_count) / total

def get_news_sentiment(symbol: str, exchange: str = "NS") -> Dict[str, Any]:
    """
    Fetches recent news for the ticker and scores the overall sentiment.
    Flags 'BREAKING_NEGATIVE' if there is extreme negative news flow.
    """
    ticker_sym = f"{symbol}.{exchange}" if exchange else symbol
    
    try:
        ticker = yf.Ticker(ticker_sym)
        news = ticker.news
        
        if not news:
            return {
                "sentiment_score": 0.0,
                "sentiment": "NEUTRAL",
                "news_count": 0,
                "flag": "NONE"
            }
            
        total_score = 0.0
        scored_articles = 0
        extreme_bear_count = 0
        
        for article in news:
            title = article.get("title", "")
            publisher = article.get("publisher", "")
            
            # Weigh publisher slightly if it's top tier
            weight = 1.0
            if "Reuters" in publisher or "Bloomberg" in publisher or "Mint" in publisher or "Economic Times" in publisher:
                weight = 1.5
                
            score = analyze_headline(title)
            
            if score != 0:
                total_score += (score * weight)
                scored_articles += 1
                
                if score <= -0.5:
                    extreme_bear_count += 1
        
        avg_score = total_score / scored_articles if scored_articles > 0 else 0.0
        
        # Determine labels
        label = "NEUTRAL"
        if avg_score >= 0.3:
            label = "BULLISH"
        elif avg_score <= -0.3:
            label = "BEARISH"
            
        # Breaking News Detector
        flag = "NONE"
        if extreme_bear_count >= 2 and avg_score <= -0.5:
            flag = "BREAKING_NEGATIVE"
        elif avg_score >= 0.7 and scored_articles >= 2:
            flag = "BREAKING_POSITIVE"
            
        return {
            "sentiment_score": round(avg_score, 2),
            "sentiment": label,
            "news_count": len(news),
            "scored_articles": scored_articles,
            "flag": flag
        }
        
    except Exception as e:
        logger.debug(f"Failed to fetch news for {symbol}: {e}")
        return {
            "sentiment_score": 0.0,
            "sentiment": "NEUTRAL",
            "news_count": 0,
            "flag": "NONE"
        }

if __name__ == "__main__":
    print(get_news_sentiment("RELIANCE"))
