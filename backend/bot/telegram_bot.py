"""
MarketPulse — Telegram Bot Module
Handles daily market summaries, alerts, and user commands.
"""
import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.stock_fetcher import get_market_overview
from data.news_fetcher import get_market_sentiment
from analysis.technical import get_technical_analysis, screen_stocks
from analysis.ml_engine import predict_symbol
from config import NIFTY_50_SYMBOLS
import database as db

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Save chat ID if not set
    if not CHAT_ID:
        env_path = Path(__file__).parent.parent.parent / ".env"
        if env_path.exists():
            content = env_path.read_text()
            if "TELEGRAM_CHAT_ID=" in content:
                content = content.replace("TELEGRAM_CHAT_ID=", f"TELEGRAM_CHAT_ID={chat_id}")
            else:
                content += f"\nTELEGRAM_CHAT_ID={chat_id}"
            env_path.write_text(content)
            
    msg = f"Hello {user.first_name}! 🚀\nI am Agent Alpha, your MarketPulse assistant.\n\nYour Chat ID ({chat_id}) has been registered for daily alerts.\n\nUse /help to see what I can do."
    await update.message.reply_text(msg)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = (
        "📈 *Agent Alpha Commands*\n\n"
        "/analyze <symbol> - Get full technical & ML analysis for a stock\n"
        "/market - Current market snapshot & sentiment\n"
        "/portfolio - Summary of your real portfolio\n"
        "/paper - Summary of your paper trading portfolio\n"
        "/screener - Top 5 stock picks for today\n"
    )
    await update.message.reply_markdown(help_text)

async def market(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get market overview."""
    await update.message.reply_text("Fetching market data...")
    
    try:
        from data.stock_fetcher import get_market_overview
        overview = get_market_overview()
        sentiment = get_market_sentiment()
        
        nifty = overview.get("NIFTY_50", {})
        nifty_change = "🟢" if nifty.get("change", 0) >= 0 else "🔴"
        
        msg = f"*Market Snapshot*\n\n"
        msg += f"{nifty_change} *NIFTY 50*: {nifty.get('value', 'N/A')} ({nifty.get('change_pct', 0):.2f}%)\n"
        msg += f"🧠 *Sentiment*: {sentiment['label']} (Score: {sentiment['score']:.2f})\n"
        msg += f"📰 *Top News*:\n"
        for i, article in enumerate(sentiment["articles"][:3], 1):
            msg += f"{i}. {article['title']}\n"
            
        await update.message.reply_markdown(msg)
    except Exception as e:
        await update.message.reply_text(f"Error fetching market data: {e}")

async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Analyze a specific stock."""
    if not context.args:
        await update.message.reply_text("Please provide a stock symbol. Usage: /analyze RELIANCE")
        return
        
    symbol = context.args[0].upper()
    await update.message.reply_text(f"Analyzing {symbol}...")
    
    try:
        ta_data = get_technical_analysis(symbol)
        if not ta_data:
            await update.message.reply_text(f"Could not find data for {symbol}.")
            return
            
        ml_data = predict_symbol(symbol)
        
        score = ta_data['score']
        signal = ta_data['signal'].replace('_', ' ')
        signal_icon = "🟢" if "BUY" in signal else "🔴" if "SELL" in signal else "🟡"
        
        msg = f"📊 *Analysis for {symbol}*\n\n"
        msg += f"*Technical Score*: {score}/100\n"
        msg += f"*Signal*: {signal_icon} {signal}\n\n"
        
        msg += f"*Levels*\n"
        msg += f"Price: ₹{ta_data['price']}\n"
        msg += f"Target: ₹{ta_data['target']}\n"
        msg += f"Stop Loss: ₹{ta_data['stop_loss']}\n\n"
        
        if ml_data:
            prob_up = ml_data['prob_up'] * 100
            ml_icon = "📈" if prob_up > 50 else "📉"
            msg += f"🤖 *ML Engine (10-day forecast)*\n"
            msg += f"Probability of UP move: {ml_icon} {prob_up:.1f}%\n"
            
        await update.message.reply_markdown(msg)
    except Exception as e:
        await update.message.reply_text(f"Error analyzing {symbol}: {e}")

async def screener(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Run screener."""
    await update.message.reply_text("Running screener... This might take a minute.")
    try:
        results = screen_stocks(NIFTY_50_SYMBOLS, top_n=5)
        
        msg = "*🏆 Top 5 Nifty Stocks Today*\n\n"
        for r in results:
            signal_icon = "🟢" if "BUY" in r['signal'] else "🔴" if "SELL" in r['signal'] else "🟡"
            msg += f"*{r['symbol']}* - {signal_icon} {r['signal'].replace('_', ' ')} (Score: {r['score']})\n"
            msg += f"Entry: ₹{r['entry']} | Target: ₹{r['target']}\n\n"
            
        await update.message.reply_markdown(msg)
    except Exception as e:
        await update.message.reply_text(f"Error running screener: {e}")

async def send_urgent_news_alert(category: str, headline: str, link: str):
    """Phase 4: Sentinel News Triage Alert Trigger"""
    if not TOKEN or not CHAT_ID:
        return
        
    import telegram
    bot = telegram.Bot(token=TOKEN)
    
    icons = {
        "CRISIS": "🚨🚨",
        "MERGER": "🤝",
        "EARNINGS": "💰",
        "BULLISH": "🟢",
        "BEARISH": "🔴"
    }
    icon = icons.get(category.upper(), "📰")
    
    msg = f"{icon} *URGENT SENTINEL ALERT* {icon}\n\n"
    msg += f"*Category*: {category.upper()}\n"
    msg += f"*Headline*: {headline}\n"
    msg += f"[Read Full Story]({link})"
    
    try:
        await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown', disable_web_page_preview=True)
    except Exception as e:
        print(f"Failed to send Sentinel alert to Telegram: {e}")

def run_bot_polling():
    """Run the bot in polling mode (for local development)."""
    if not TOKEN:
        print("TELEGRAM_BOT_TOKEN not found in environment.")
        return
        
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("market", market))
    application.add_handler(CommandHandler("analyze", analyze))
    application.add_handler(CommandHandler("screener", screener))

    print("Agent Alpha Telegram Bot starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    run_bot_polling()
