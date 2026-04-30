import os
import asyncio
import sys
from pathlib import Path
from telegram import Bot

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.stock_fetcher import get_market_overview
from data.news_fetcher import get_market_sentiment
from analysis.technical import screen_stocks
from config import NIFTY_50_SYMBOLS, USER_MF_HOLDINGS
import requests

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

async def send_daily_alert():
    if not TOKEN or not CHAT_ID:
        print("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
        return

    bot = Bot(token=TOKEN)
    
    # 1. Market Snapshot
    print("Fetching market data...")
    overview = get_market_overview()
    sentiment = get_market_sentiment()
    
    nifty = overview.get("NIFTY_50", {})
    nifty_change = "🟢" if nifty.get("change", 0) >= 0 else "🔴"
    
    msg = f"🌅 *Agent Alpha Daily Briefing*\n\n"
    msg += f"{nifty_change} *NIFTY 50*: {nifty.get('value', 'N/A')} ({nifty.get('change_pct', 0):.2f}%)\n"
    msg += f"🧠 *Sentiment*: {sentiment['label']} (Score: {sentiment['score']:.2f})\n\n"
    
    # 2. Portfolio Update (Stateless via config)
    print("Fetching portfolio data...")
    total_inv = 0
    total_cur = 0
    msg += "*💼 Portfolio Update*\n"
    for name, info in USER_MF_HOLDINGS.items():
        try:
            code = info["scheme_code"]
            invested = info["invested"]
            resp = requests.get(f"https://api.mfapi.in/mf/{code}/latest").json()
            nav = float(resp["data"][0]["nav"])
            # Approximate units if not exact, but good enough for daily tracking
            units = info.get("units") or (invested / nav) # We'll need exact units in config ideally
            current = units * nav
            
            total_inv += invested
            total_cur += current
            
            pnl = current - invested
            icon = "🟢" if pnl >= 0 else "🔴"
            msg += f"{icon} {name[:15]}..: ₹{current:,.0f}\n"
        except Exception as e:
            pass
            
    total_pnl = total_cur - total_inv
    total_pct = (total_pnl / total_inv) * 100 if total_inv else 0
    pnl_icon = "🟢" if total_pnl >= 0 else "🔴"
    msg += f"\n*Net Value*: ₹{total_cur:,.0f}\n"
    msg += f"*Total P&L*: {pnl_icon} ₹{total_pnl:,.0f} ({total_pct:.2f}%)\n\n"

    # 3. Screener Top 3
    print("Running screener...")
    results = screen_stocks(NIFTY_50_SYMBOLS, top_n=3)
    msg += "*🎯 Top 3 Actionable Stocks Today*\n"
    for r in results:
        signal_icon = "🟢" if "BUY" in r['signal'] else "🔴" if "SELL" in r['signal'] else "🟡"
        msg += f"{signal_icon} *{r['symbol']}* (AI Score: {r['score']}/100)\n"
        msg += f"👉 Buy at: ₹{r['entry']} | Target (Sell): ₹{r['target']}\n\n"

    # 4. Agent's Advice (What to do)
    msg += "💡 *Agent's Advice for You*\n"
    if nifty.get("change", 0) > 0 and sentiment['score'] > 0:
        msg += "• *Market Condition*: The market is positive and sentiment is bullish. This is a good time to hold your current Mutual Funds. Do not panic sell.\n"
    elif nifty.get("change", 0) < 0 and sentiment['score'] < 0:
        msg += "• *Market Condition*: The market is down and sentiment is bearish. This is normal. Your Mutual Funds are long-term investments; ignore the short-term noise.\n"
    else:
        msg += "• *Market Condition*: The market is mixed. Hold your positions steady.\n"
        
    if results:
        top_pick = results[0]['symbol']
        msg += f"• *Paper Trading*: Consider opening the dashboard and executing a Paper Trade for *{top_pick}* to see if our system's BUY signal is accurate!"

    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")
    print("Daily alert sent successfully!")

if __name__ == "__main__":
    asyncio.run(send_daily_alert())
