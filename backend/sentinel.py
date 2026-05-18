"""
Agent Alpha v4.0 - Sentinel Daemon
Runs independently (e.g., on Windows laptop) polling RSS feeds and triaging news 
using local Llama 3.1 8B via Ollama.
"""
import time
import requests
import json
import logging
from datetime import datetime
import feedparser

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Sentinel")

OLLAMA_URL = "http://localhost:11434/api/generate"
# Modify this if backend is hosted elsewhere
BACKEND_URL = "http://localhost:8000" 

RSS_FEEDS = [
    "https://economictimes.indiatimes.com/markets/rssfeeds/2146842.cms",
    "https://www.moneycontrol.com/rss/marketreports.xml"
]

SEEN_URLS = set()

def triage_news(headline: str, summary: str) -> str:
    """Uses Llama 3.1 8B to classify the news."""
    prompt = f"""
    You are an institutional financial analyst. Classify the following news into ONE of these categories:
    [BULLISH, BEARISH, CRISIS, MERGER, EARNINGS, IRRELEVANT]
    
    News Headline: {headline}
    Summary: {summary}
    
    Return ONLY the category word. No explanation.
    """
    try:
        res = requests.post(OLLAMA_URL, json={
            "model": "llama3.1",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.0
            }
        }, timeout=15)
        
        if res.status_code == 200:
            category = res.json().get("response", "").strip().upper()
            valid = ["BULLISH", "BEARISH", "CRISIS", "MERGER", "EARNINGS", "IRRELEVANT"]
            for v in valid:
                if v in category:
                    return v
            return "IRRELEVANT"
    except Exception as e:
        logger.error(f"Ollama classification failed: {e}")
        return "IRRELEVANT"
    return "IRRELEVANT"

def trigger_alert(category: str, headline: str, link: str):
    """Trigger the main backend alert endpoint."""
    try:
        # In a real setup, we might have a specific endpoint for pushing news alerts
        # For now, we simulate an urgent push to the bot/alert (or a custom endpoint)
        payload = {
            "type": "URGENT_NEWS",
            "category": category,
            "headline": headline,
            "link": link
        }
        res = requests.post(f"{BACKEND_URL}/api/bot/alert/news", json=payload, timeout=10)
        if res.status_code == 200:
            logger.info(f"Alert successfully dispatched for: {headline}")
        else:
            logger.warning(f"Backend returned {res.status_code} for alert.")
    except Exception as e:
        logger.error(f"Failed to trigger backend alert: {e}")

def run_sentinel():
    logger.info("🛡️ Sentinel Daemon Started. Monitoring RSS Feeds...")
    while True:
        try:
            for feed_url in RSS_FEEDS:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:5]: # Check top 5
                    if entry.link not in SEEN_URLS:
                        SEEN_URLS.add(entry.link)
                        if len(SEEN_URLS) > 1000:
                            # Keep set from growing infinitely
                            SEEN_URLS.clear() 
                            
                        headline = entry.get('title', '')
                        summary = entry.get('summary', '')
                        
                        logger.info(f"Scanning: {headline}")
                        category = triage_news(headline, summary)
                        logger.info(f"Classification: {category}")
                        
                        if category in ["CRISIS", "MERGER", "EARNINGS"]:
                            logger.critical(f"🚨 URGENT NEWS DETECTED: {category} - {headline}")
                            trigger_alert(category, headline, entry.link)
                            
        except Exception as e:
            logger.error(f"Sentinel error: {e}")
            
        # Poll every 5 minutes
        time.sleep(300)

if __name__ == "__main__":
    run_sentinel()
