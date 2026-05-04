import sys
import os
import asyncio
from pathlib import Path
import ssl
import traceback

# Fix SSL issues
ssl._create_default_https_context = ssl._create_unverified_context

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from telegram import Bot
from analysis.advisor import generate_financial_advice
import database as db
from data.stock_fetcher import get_market_overview
from data.news_fetcher import get_market_news

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_sync(msg):
    """Synchronous wrapper to send Telegram message."""
    import requests
    if not TOKEN or not CHAT_ID:
        return False
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code != 200:
            # Telegram rejected the Markdown, try sending as plain text
            print(f"Markdown failed ({r.status_code}), retrying plain text...")
            payload.pop("parse_mode")
            r = requests.post(url, json=payload, timeout=10)
        return r.status_code == 200
    except Exception:
        return False

async def send_daily_alert():
    """Fetches data, generates AI advice, and sends the daily Telegram briefing."""
    print("🚀 Triggering Agent Alpha AI Briefing...")
    
    try:
        # 1. Fetch Market Context
        try:
            market_data = get_market_overview()
            market_text = "\n".join([f"{k}: {v['value']} ({v['change_pct']}%)" for k, v in market_data.items() if v])
        except Exception:
            market_text = "Market data temporarily unavailable."

        # 2. Fetch News
        try:
            news = get_market_news(max_results=5)
            news_text = "\n".join([f"- {n['title']} (Sentiment: {n['sentiment']})" for n in news])
        except Exception:
            news_text = "News data temporarily unavailable."

        # 3. Fetch Portfolio
        try:
            holdings = db.get_holdings()
            portfolio_text = "\n".join([f"- {h['name']} ({h['asset_type']}): {h['quantity']} units @ {h['buy_price']}" for h in holdings])
            if not portfolio_text:
                portfolio_text = "Portfolio is currently empty."
        except Exception:
            portfolio_text = "Portfolio data temporarily unavailable."

        # 4. Generate AI Advice
        advice_markdown = generate_financial_advice(portfolio_text, market_text, news_text)

        # 5. Send to Telegram
        success = send_telegram_sync(advice_markdown)
        if success:
            print("✅ Daily AI briefing sent successfully.")
        else:
            print("❌ Failed to send Telegram message.")
            
    except Exception as e:
        # DEAD MAN'S SWITCH / FALLBACK
        print(f"❌ FATAL ERROR in daily_job: {traceback.format_exc()}")
        fallback_msg = f"⚠️ *Agent Alpha Alert*\nI encountered a critical error while trying to generate your daily financial plan. I am still online, but my data feeds or AI engine timed out.\n\n`{str(e)}`"
        send_telegram_sync(fallback_msg)

if __name__ == "__main__":
    asyncio.run(send_daily_alert())
