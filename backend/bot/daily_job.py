"""
MarketPulse — Daily Job Engine (v2.0)
Gathers rich market data, portfolio values, and screener results,
then feeds everything to the AI Advisor for a comprehensive briefing.
Runs as a cron job on Render (8:00 AM & 2:45 PM IST).
"""
import sys
import os
import asyncio
from pathlib import Path
import ssl
import traceback
from datetime import datetime

# Fix SSL issues
ssl._create_default_https_context = ssl._create_unverified_context

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from telegram import Bot
from analysis.advisor import generate_financial_advice
import database as db
from data.stock_fetcher import get_market_overview
from data.news_fetcher import get_market_news
from data.mf_fetcher import get_mf_nav, get_mf_portfolio_value
from config import NIFTY_50_SYMBOLS, USER_MF_HOLDINGS

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()


def send_telegram_sync(msg):
    """Synchronous wrapper to send Telegram message via HTTP."""
    import requests
    if not TOKEN or not CHAT_ID:
        print("❌ TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set!")
        return False
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    # Telegram max length is 4096. Split into 4000 char chunks to be safe.
    chunks = [msg[i:i+4000] for i in range(0, len(msg), 4000)]
    all_success = True

    for i, chunk in enumerate(chunks):
        payload = {"chat_id": CHAT_ID, "text": chunk, "parse_mode": "Markdown"}
        try:
            r = requests.post(url, json=payload, timeout=15)
            if r.status_code != 200:
                # Telegram rejected the Markdown, try sending as plain text
                print(f"Markdown failed ({r.status_code}: {r.text[:100]}), retrying plain text...")
                payload.pop("parse_mode")
                r = requests.post(url, json=payload, timeout=15)
            if r.status_code != 200:
                print(f"Failed to send chunk {i+1}/{len(chunks)}: {r.text[:200]}")
                all_success = False
            else:
                print(f"✅ Sent chunk {i+1}/{len(chunks)}")
        except Exception as e:
            print(f"Exception sending chunk {i+1}: {e}")
            all_success = False

    return all_success


def _detect_session_type():
    """Determine if this is a morning or afternoon briefing based on current IST time."""
    try:
        from zoneinfo import ZoneInfo
        ist_now = datetime.now(ZoneInfo("Asia/Kolkata"))
    except ImportError:
        # Fallback: assume server is in UTC, IST = UTC + 5:30
        import pytz
        ist_now = datetime.now(pytz.timezone("Asia/Kolkata"))
    except Exception:
        ist_now = datetime.utcnow()

    hour = ist_now.hour
    if hour < 12:
        return "morning"
    else:
        return "afternoon"


def _gather_portfolio_data():
    """
    Gather portfolio data. Try DB first, fall back to config.py hardcoded holdings.
    This ensures we ALWAYS have portfolio context even if DB is unreachable.
    """
    # Attempt 1: From database
    try:
        db.init_db()
        holdings = db.get_holdings()
        if holdings and len(holdings) > 0:
            lines = []
            for h in holdings:
                lines.append(
                    f"- {h['name']} ({h['asset_type'].upper()}) | "
                    f"Invested: ₹{h['invested_amount']:,.0f} | "
                    f"Units: {h['quantity']:.4f} | "
                    f"Scheme Code: {h.get('scheme_code', 'N/A')}"
                )
            portfolio_text = "\n".join(lines)
            print(f"✅ Portfolio from DB: {len(holdings)} holdings")
        else:
            raise Exception("DB returned empty holdings")
    except Exception as db_err:
        print(f"⚠️ DB portfolio failed ({db_err}), using hardcoded config...")
        # Attempt 2: From config.py (ALWAYS available)
        lines = []
        for name, info in USER_MF_HOLDINGS.items():
            lines.append(
                f"- {name} (MF) | "
                f"Invested: ₹{info['invested']:,.0f} | "
                f"Units: {info['units']:.4f} | "
                f"Scheme Code: {info['scheme_code']}"
            )
        portfolio_text = "\n".join(lines)
        print(f"✅ Portfolio from config: {len(USER_MF_HOLDINGS)} holdings")

    # Enrich with live NAV data
    try:
        mf_list = [
            {"scheme_code": info["scheme_code"], "invested": info["invested"], "units": info["units"]}
            for info in USER_MF_HOLDINGS.values()
        ]
        mf_values = get_mf_portfolio_value(mf_list)
        if mf_values and mf_values.get("holdings"):
            portfolio_text += "\n\n📈 LIVE MF VALUES (returns are TOTAL since purchase, NOT daily change):\n"
            for h in mf_values["holdings"]:
                portfolio_text += (
                    f"- {h['scheme_name']}: NAV ₹{h['nav']:.2f} | "
                    f"Current Value: ₹{h['current_value']:,.2f} | "
                    f"Returns: {h['returns']:+.2f}% (₹{h['returns_abs']:+,.2f})\n"
                )
            portfolio_text += (
                f"\n💰 TOTAL: Invested ₹{mf_values['total_invested']:,.0f} → "
                f"Current ₹{mf_values['total_current']:,.2f} | "
                f"Returns: {mf_values['total_returns_pct']:+.2f}% "
                f"(₹{mf_values['total_returns']:+,.2f})"
            )
            print(f"✅ Live MF values fetched successfully")
    except Exception as nav_err:
        print(f"⚠️ Live NAV fetch failed: {nav_err}")
        portfolio_text += "\n(Live NAV values temporarily unavailable)"

    return portfolio_text


def _gather_market_data():
    """Gather comprehensive market data."""
    try:
        market_data = get_market_overview()
        if not market_data:
            return "Market data temporarily unavailable (market may be closed)."

        lines = []
        display_names = {
            "NIFTY_50": "🇮🇳 Nifty 50",
            "SENSEX": "🇮🇳 Sensex",
            "NIFTY_BANK": "🏦 Bank Nifty",
            "S&P_500": "🇺🇸 S&P 500",
            "NASDAQ": "🇺🇸 Nasdaq",
            "INDIA_VIX": "😰 India VIX (Fear Gauge)",
            "GOLD_USD": "🥇 Gold (USD/oz)",
            "CRUDE_OIL": "🛢️ Crude Oil (USD/bbl)",
            "USD_INR": "💱 USD/INR",
        }
        for key, val in market_data.items():
            name = display_names.get(key, key)
            direction = "▲" if val["change"] >= 0 else "▼"
            lines.append(
                f"{name}: {val['value']:,.2f} {direction} {abs(val['change']):.2f} ({val['change_pct']:+.2f}%)"
            )
        market_text = "\n".join(lines)
        print(f"✅ Market data: {len(market_data)} indices/commodities")
        return market_text

    except Exception as e:
        print(f"⚠️ Market data failed: {e}")
        return "Market data temporarily unavailable."


def _gather_news_data():
    """Gather and format news with sentiment."""
    try:
        news = get_market_news(max_results=8)
        if not news:
            return "No news available today."

        lines = []
        for n in news:
            sentiment_emoji = "🟢" if n["sentiment"] == "positive" else "🔴" if n["sentiment"] == "negative" else "⚪"
            lines.append(f"{sentiment_emoji} {n['title']} (Sentiment: {n['sentiment']}, Score: {n['sentiment_score']:.2f})")

        news_text = "\n".join(lines)
        print(f"✅ News: {len(news)} articles")
        return news_text

    except Exception as e:
        print(f"⚠️ News failed: {e}")
        return "News data temporarily unavailable."


def _gather_screener_data(top_n=5):
    """Run the stock screener and format results for the AI."""
    try:
        from analysis.technical import screen_stocks
        # Run screener ONCE on all stocks, then slice for top + dip candidates
        all_results = screen_stocks(NIFTY_50_SYMBOLS, top_n=50)
        if not all_results:
            return ""

        # Top N by score (best stocks)
        top_results = all_results[:top_n]
        lines = [f"Top {len(top_results)} Nifty 50 Stocks by Technical Score:\n"]
        for i, r in enumerate(top_results, 1):
            signal_emoji = "🟢" if "BUY" in r["signal"] else "🔴" if "SELL" in r["signal"] else "🟡"
            lines.append(
                f"{i}. {r['symbol']} — {signal_emoji} {r['signal'].replace('_', ' ')} | "
                f"Score: {r['score']}/100 | "
                f"Price: ₹{r['price']:,.2f} | "
                f"Entry: ₹{r['entry']:,.2f} | "
                f"Target: ₹{r['target']:,.2f} | "
                f"Stop Loss: ₹{r['stop_loss']:,.2f} | "
                f"RSI: {r['indicators'].get('rsi', 'N/A')}"
            )

        # Dip candidates from the SAME results (no second screener run)
        dip_candidates = [r for r in all_results if r["score"] <= 35]
        if dip_candidates:
            lines.append("\n⚠️ OVERSOLD / DIP CANDIDATES (Low scores may = buying opportunity):")
            for r in dip_candidates[:3]:
                lines.append(
                    f"- {r['symbol']} — Score: {r['score']}/100 | "
                    f"Price: ₹{r['price']:,.2f} | RSI: {r['indicators'].get('rsi', 'N/A')} | "
                    f"Signal: {r['signal'].replace('_', ' ')}"
                )

        screener_text = "\n".join(lines)
        print(f"✅ Screener: {len(top_results)} top + {len(dip_candidates)} dip candidates")
        return screener_text

    except Exception as e:
        print(f"⚠️ Screener failed: {e}")
        return ""


async def send_daily_alert():
    """Master function: Gathers ALL data, generates AI advice, sends to Telegram."""
    print("=" * 60)
    print(f"🚀 Agent Alpha Briefing Engine Starting — {datetime.now().isoformat()}")
    print("=" * 60)

    result = {"steps": []}

    try:
        # 0. Determine session type
        session_type = _detect_session_type()
        print(f"📋 Session Type: {session_type.upper()}")
        result["steps"].append(f"✅ Session: {session_type}")

        # 1. Gather Portfolio (ALWAYS succeeds due to config.py fallback)
        print("\n── Step 1: Portfolio ──")
        portfolio_text = _gather_portfolio_data()
        result["steps"].append(f"✅ Portfolio gathered")

        # 2. Gather Market Data
        print("\n── Step 2: Market Data ──")
        market_text = _gather_market_data()
        result["steps"].append(f"✅ Market data gathered")

        # 3. Gather News
        print("\n── Step 3: News & Sentiment ──")
        news_text = _gather_news_data()
        result["steps"].append(f"✅ News gathered")

        # 4. Run Screener (morning only — takes 1-2 mins, skip for afternoon speed)
        print("\n── Step 4: Screener ──")
        if session_type == "morning":
            screener_text = _gather_screener_data(top_n=5)
            result["steps"].append(f"✅ Screener completed")
        else:
            screener_text = ""
            result["steps"].append("⏭️ Screener skipped (afternoon session)")

        # 5. Generate AI Advice
        print("\n── Step 5: Generating AI Advice ──")
        advice_markdown = generate_financial_advice(
            portfolio_data=portfolio_text,
            market_data=market_text,
            news_data=news_text,
            screener_data=screener_text,
            session_type=session_type,
        )
        result["steps"].append(f"✅ AI advice generated: {len(advice_markdown)} chars")
        result["advice_preview"] = advice_markdown[:300]
        print(f"✅ Advice generated ({len(advice_markdown)} chars)")

        # 6. Send to Telegram
        print("\n── Step 6: Sending to Telegram ──")
        success = send_telegram_sync(advice_markdown)
        if success:
            print("✅ Daily AI briefing sent successfully!")
            result["steps"].append("✅ Telegram sent successfully")
            result["status"] = "success"
        else:
            print("❌ Failed to send Telegram message")
            result["steps"].append("❌ Telegram send FAILED")
            result["status"] = "telegram_failed"

    except Exception as e:
        # DEAD MAN'S SWITCH — if everything crashes, still send a basic alert
        print(f"\n❌ FATAL ERROR in daily_job: {traceback.format_exc()}")
        result["steps"].append(f"❌ FATAL: {e}")
        result["status"] = "fatal_error"

        fallback_msg = (
            f"⚠️ *Agent Alpha — Emergency Alert*\n\n"
            f"Bhai, I ran into a critical error while preparing your briefing.\n\n"
            f"*Error:* {str(e)[:200]}\n\n"
            f"📋 *Manual Checklist:*\n"
            f"1. Open Groww → Check your 3 MF NAVs\n"
            f"2. Check Nifty 50 on Google → Above/below 22,000?\n"
            f"3. If Nifty dropped >1%, consider adding ₹2,000 to your index SIP\n"
            f"4. I'll fix myself and be back next briefing. 🙏"
        )
        send_telegram_sync(fallback_msg)

    print("\n" + "=" * 60)
    print(f"🏁 Briefing Engine Complete — Status: {result.get('status', 'unknown')}")
    print("Steps:", "\n  ".join(result.get("steps", [])))
    print("=" * 60)

    return result


if __name__ == "__main__":
    asyncio.run(send_daily_alert())
