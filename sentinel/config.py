"""
Sentinel Configuration
"""
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1"

WS_HOST = "0.0.0.0"
WS_PORT = 9090

# Alert Thresholds (Severity out of 10)
THRESHOLDS = {
    "MACRO": 0,
    "REGULATORY": 0,
    "EARNINGS": 0,
    "INSIDER": 0,
    "SECTOR": 0
}

RSS_FEEDS = [
    "https://economictimes.indiatimes.com/markets/rssfeeds/2146842.cms",
    "https://www.moneycontrol.com/rss/marketreports.xml",
    "https://www.livemint.com/rss/markets",
    "https://www.business-standard.com/rss/markets-106.rss",
    "https://www.cnbctv18.com/api/v1/rss/market.xml",
    "https://www.nseindia.com/api/corporate-announcements" # Placeholder representation for NSE
]
