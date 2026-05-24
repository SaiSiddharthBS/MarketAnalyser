"""
Agent Alpha v4.0 - Sentinel Daemon (Windows)
Polls RSS feeds, classifies using Llama 3.1 8B, and broadcasts via WS.
"""
import time
import requests
import json
import logging
import asyncio
import threading
import sqlite3
import os
from dotenv import load_dotenv
from datetime import datetime
from config import OLLAMA_URL, OLLAMA_MODEL, THRESHOLDS

# Load .env from parent directory
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
from feed_poller import get_latest_headlines
from ws_server import broadcast_alert_threadsafe, run_ws_server_in_thread

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Sentinel")

def init_db():
    conn = sqlite3.connect("sentinel_alerts.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        severity INTEGER,
        headline TEXT,
        link TEXT,
        symbols TEXT,
        reason TEXT,
        timestamp TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

SEEN_URLS_FILE = "seen_urls.txt"
if os.path.exists(SEEN_URLS_FILE):
    with open(SEEN_URLS_FILE, "r", encoding="utf-8") as f:
        SEEN_URLS = set(f.read().splitlines())
else:
    SEEN_URLS = set()

def save_seen_urls():
    with open(SEEN_URLS_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(list(SEEN_URLS)[-2000:]))

def triage_news(headline: str, summary: str) -> dict:
    """Uses Llama 3.3 70B via Groq to classify the news."""
    prompt = f"""
    You are an elite quantitative financial analyst for the Indian stock market (NSE/BSE).
    CLASSIFY THE FOLLOWING NEWS: "{headline}"
    
    SEVERITY RUBRIC (1-10):
    1-3: Routine daily market chatter, minor updates, standard dividends.
    4-6: Notable shifts, large earnings beats/misses, important sector news.
    7-8: Major regulatory crackdowns, massive block deals, CEO resignations, deep market drops.
    9-10: Market-crashing black swan events, massive fraud, wars. (BE EXTREMELY CONSERVATIVE with 8-10).
    
    Reply ONLY with this exact JSON structure:
    {{"m":true/false,"s":1-10,"t":["SYMBOL"],"c":"EARNINGS|REGULATORY|MACRO|INSIDER|SECTOR","r":"10 words max"}}
    """
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", json={
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "You are a JSON-only financial API. Always output valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.0,
            "response_format": {"type": "json_object"}
        }, headers=headers, timeout=10)
        
        if res.status_code == 200:
            text = res.json()["choices"][0]["message"]["content"].strip()
            # Groq returns clean JSON due to response_format
            return json.loads(text)
        else:
            logger.error(f"Groq API Error: {res.text}")
    except Exception as e:
        logger.error(f"Groq classification failed: {e}")
    return {}

def run_sentinel():
    logger.info("🛡️ Sentinel Daemon Started. Monitoring RSS Feeds...")
    while True:
        try:
            headlines = get_latest_headlines()
            for entry in headlines:
                if entry['link'] not in SEEN_URLS:
                    SEEN_URLS.add(entry['link'])
                    save_seen_urls()
                    if len(SEEN_URLS) > 2000:
                        SEEN_URLS.clear()
                        save_seen_urls()
                        
                    logger.info(f"Scanning: {entry['headline']}")
                    classification = triage_news(entry['headline'], entry['summary'])
                    
                    if classification:
                        cat = classification.get("c", "NONE")
                        severity = classification.get("s", 0)
                        threshold = THRESHOLDS.get(cat, 11) # Default 11 = never alert
                        
                        logger.info(f"Classified as {cat} (Sev: {severity})")
                        
                        if severity >= threshold:
                            logger.critical(f"🚨 URGENT NEWS DETECTED: {cat} ({severity}/10) - {entry['headline']}")
                            
                            conn = sqlite3.connect("sentinel_alerts.db")
                            c = conn.cursor()
                            c.execute('''INSERT INTO alerts 
                                (category, severity, headline, link, symbols, reason, timestamp) 
                                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                                (cat, severity, entry['headline'], entry['link'], json.dumps(classification.get("t", [])), classification.get("r", ""), datetime.now().isoformat()))
                            conn.commit()
                            conn.close()

                            alert_data = {
                                "type": "URGENT_NEWS",
                                "category": cat,
                                "severity": severity,
                                "headline": entry['headline'],
                                "link": entry['link'],
                                "symbols": classification.get("t", []),
                                "reason": classification.get("r", "")
                            }
                            broadcast_alert_threadsafe(alert_data)
                            
                            # Send Telegram Alert
                            if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
                                try:
                                    tg_msg = f"🚨 *SENTINEL ALERT* 🚨\n\n*Category*: {cat}\n*Severity*: {severity}/10\n*Headline*: {entry['headline']}\n\n*Reason*: {classification.get('r', '')}\n[Read more]({entry['link']})"
                                    tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                                    requests.post(tg_url, json={
                                        "chat_id": TELEGRAM_CHAT_ID,
                                        "text": tg_msg,
                                        "parse_mode": "Markdown"
                                    }, timeout=5)
                                except Exception as e:
                                    logger.error(f"Failed to send Telegram alert: {e}")
                            
        except Exception as e:
            logger.error(f"Sentinel error: {e}")
            
        # Poll every 5 minutes
        time.sleep(300)

def main():
    logger.info("Starting WS Server in background thread...")
    ws_thread = threading.Thread(target=run_ws_server_in_thread, daemon=True)
    ws_thread.start()
    
    # Run sentinel polling loop in main thread
    run_sentinel()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("🛑 Sentinel Shutdown Requested. Closing connections...")
        # Optional: gracefully close WS server or any other threads
        import os
        os._exit(0) # Force hard exit to kill daemon threads instantly
