"""
MarketPulse — Agent Alpha
Main FastAPI Application
"""
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.concurrency import run_in_threadpool
import uvicorn
import asyncio
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import traceback

import database as db
from data import stock_fetcher, news_fetcher
from data.stock_fetcher import (
    get_stock_data, get_stock_info, get_market_overview,
    get_ltp, get_bulk_ltp
)
from data.mf_fetcher import get_mf_nav, get_mf_historical, get_mf_portfolio_value
from data.news_fetcher import get_market_sentiment, get_stock_news, get_market_news
from analysis.technical import get_technical_analysis, screen_stocks
from config import NIFTY_50_SYMBOLS, USER_MF_HOLDINGS, SECTOR_INDICES, SIGNAL_LABELS

app = FastAPI(title="MarketPulse - Agent Alpha", version="3.0.0")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.on_event("startup")
async def startup():
    try:
        db.init_db()
        _seed_portfolio()
    except Exception as e:
        print(f"⚠️ Startup error (non-fatal): {e}")


def _seed_portfolio():
    """Pre-load user's MF holdings if DB is empty."""
    try:
        holdings = db.get_holdings()
        if not holdings:
            for name, info in USER_MF_HOLDINGS.items():
                db.add_holding(
                    symbol=info["scheme_code"],
                    name=name,
                    asset_type="mf",
                    quantity=info.get("units", 0),
                    buy_price=0,
                    buy_date="2025-01-01",
                    invested_amount=info["invested"],
                    scheme_code=info["scheme_code"],
                )
            print("✅ Pre-loaded user MF holdings")
    except Exception as e:
        print(f"⚠️ Seed error: {e}")


# ─── Frontend Routes ─────────────────────────────────────

@app.get("/")
async def serve_frontend():
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"message": "MarketPulse API is running. Frontend not found."}


# ─── Market Overview ─────────────────────────────────────

@app.get("/api/market/overview")
async def market_overview():
    """Get Nifty 50, Sensex and Global Market status."""
    try:
        # Fetch in parallel to prevent timeouts
        indices_task = run_in_threadpool(stock_fetcher.get_market_overview)
        news_task = run_in_threadpool(news_fetcher.get_market_news)
        sentiment_task = run_in_threadpool(news_fetcher.get_market_sentiment)

        try:
            indices, news, sentiment = await asyncio.wait_for(
                asyncio.gather(indices_task, news_task, sentiment_task, return_exceptions=True),
                timeout=45.0
            )
        except asyncio.TimeoutError:
            print("⚠️ Market overview fetch timed out!")
            indices, news, sentiment = Exception("Timeout"), Exception("Timeout"), Exception("Timeout")

        # Handle partial failures gracefully
        if isinstance(indices, Exception):
            print(f"⚠️ Indices fetch failed: {indices}")
            indices = {}
        if isinstance(news, Exception):
            print(f"⚠️ News fetch failed: {news}")
            news = []
        if isinstance(sentiment, Exception):
            print(f"⚠️ Sentiment fetch failed: {sentiment}")
            sentiment = {"score": 0, "label": "Unavailable", "positive_pct": 0, "negative_pct": 0}

        return {
            "timestamp": datetime.now().isoformat(),
            "indices": indices or {},
            "sentiment": {
                "score": sentiment.get("score", 0) if isinstance(sentiment, dict) else 0,
                "label": sentiment.get("label", "Unavailable") if isinstance(sentiment, dict) else "Unavailable",
                "positive_pct": sentiment.get("positive_pct", 0) if isinstance(sentiment, dict) else 0,
                "negative_pct": sentiment.get("negative_pct", 0) if isinstance(sentiment, dict) else 0,
            },
            "news": (news if isinstance(news, list) else [])[:15],
        }
    except Exception as e:
        print(f"❌ Market overview error: {traceback.format_exc()}")
        return {
            "timestamp": datetime.now().isoformat(),
            "indices": {},
            "sentiment": {"score": 0, "label": "Error", "positive_pct": 0, "negative_pct": 0},
            "news": [],
            "error": str(e),
        }


@app.get("/api/market/index/{symbol}")
async def index_data(symbol: str, period: str = "6mo"):
    """Get index chart data."""
    try:
        data = await run_in_threadpool(get_stock_data, symbol, period=period, exchange="")
        if not data:
            raise HTTPException(404, f"No data for {symbol}")
        return {"symbol": symbol, "data": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error fetching {symbol}: {str(e)}")


# ─── Stock Analysis ──────────────────────────────────────

def _find_sector_for_symbol(symbol):
    """Find which sector a stock belongs to and return its yahoo index."""
    for key, seg in SECTOR_INDICES.items():
        if symbol.upper() in seg["symbols"]:
            return seg.get("yahoo_index", "^NSEI")
    return "^NSEI"

@app.get("/api/stock/{symbol}")
async def stock_detail(symbol: str):
    """Get full analysis for a stock."""
    try:
        sector_idx = _find_sector_for_symbol(symbol)
        info_task = run_in_threadpool(get_stock_info, symbol)
        ta_task = run_in_threadpool(get_technical_analysis, symbol, "NS", "1y", sector_idx)
        news_task = run_in_threadpool(get_stock_news, symbol)

        info, ta_result, news = await asyncio.gather(
            info_task, ta_task, news_task,
            return_exceptions=True
        )

        return {
            "info": info if not isinstance(info, Exception) else None,
            "technical": ta_result if not isinstance(ta_result, Exception) else None,
            "news": (news[:5] if isinstance(news, list) else []),
        }
    except Exception as e:
        raise HTTPException(500, f"Error analysing {symbol}: {str(e)}")


@app.get("/api/stock/{symbol}/chart")
async def stock_chart(symbol: str, period: str = "1y"):
    """Get price chart data."""
    try:
        # Map periods to appropriate intervals
        interval_map = {"1d": "5m", "5d": "15m", "1mo": "1d", "6mo": "1d", "1y": "1d", "5y": "1wk", "max": "1mo"}
        interval = interval_map.get(period, "1d")
        data = await run_in_threadpool(get_stock_data, symbol, period=period, interval=interval)
        if not data:
            raise HTTPException(404, f"No data for {symbol}")
        # Filter out records with null OHLC
        clean = [d for d in data if d.get("Open") and d.get("Close") and d.get("High") and d.get("Low")]
        return {"symbol": symbol, "period": period, "data": clean}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error fetching chart for {symbol}: {str(e)}")


# ─── Screener ────────────────────────────────────────────

@app.get("/api/screener/segments")
async def screener_segments():
    """List all available screener segments."""
    return [
        {"key": k, "name": v["name"], "count": len(v["symbols"])}
        for k, v in SECTOR_INDICES.items()
    ]


@app.get("/api/screener/top")
async def screener_top(n: int = 10, segment: str = "NIFTY_50"):
    """Get top N stocks by technical score from a segment."""
    try:
        if segment == "ALL_SECTORS":
            # Scan top 3 from each sector, merge and rank
            all_results = []
            for seg_key, seg_data in SECTOR_INDICES.items():
                try:
                    symbols = seg_data["symbols"][:15]  # Limit per sector for speed
                    yahoo_idx = seg_data.get("yahoo_index", "^NSEI")
                    results = await run_in_threadpool(screen_stocks, symbols, top_n=3, sector_yahoo_index=yahoo_idx)
                    for r in results:
                        r["sector_name"] = seg_data["name"]
                    all_results.extend(results)
                except Exception as seg_err:
                    print(f"⚠️ Skipping {seg_key}: {seg_err}")
            phase_priority = {"EARLY_MOMENTUM": 6, "CONTINUATION": 5, "PULLBACK": 4, "EXTENDED": 3, "WEAK": 2, "AVOID": 1}
            all_results.sort(key=lambda x: (phase_priority.get(x["signal"], 0), x["score"]), reverse=True)
            # Deduplicate by symbol (keep highest score)
            seen = set()
            deduped = []
            for r in all_results:
                if r["symbol"] not in seen:
                    seen.add(r["symbol"])
                    deduped.append(r)
            all_results = deduped[:n]
            return {
                "segment": "ALL_SECTORS",
                "segment_name": "🔥 All Sectors — Top Picks",
                "count": len(all_results),
                "stocks": all_results,
                "signal_labels": SIGNAL_LABELS,
            }

        seg_data = SECTOR_INDICES.get(segment)
        if not seg_data:
            return {"count": 0, "stocks": [], "error": f"Unknown segment: {segment}"}

        symbols = seg_data["symbols"]
        yahoo_index = seg_data.get("yahoo_index", "^NSEI")
        results = await run_in_threadpool(
            screen_stocks, symbols, top_n=n, sector_yahoo_index=yahoo_index
        )

        # Log signals for accuracy tracking (Day 1)
        try:
            import database as db
            db.log_screener_signals(results, segment=segment)
        except Exception as log_err:
            print(f"⚠️ Signal logging failed: {log_err}")

        return {
            "segment": segment,
            "segment_name": seg_data["name"],
            "count": len(results),
            "stocks": results,
            "signal_labels": SIGNAL_LABELS,
        }
    except Exception as e:
        print(f"❌ Screener error: {e}")
        return {"count": 0, "stocks": [], "error": str(e)}


# ─── Market Regime ───────────────────────────────────────

@app.get("/api/market/regime")
async def market_regime():
    """Get current market regime for the global bar."""
    try:
        from analysis.technical import _fetch_market_context
        ctx = _fetch_market_context()
        vix = ctx.get("vix")
        nifty_bullish = ctx.get("nifty_above_50ema", False)
        regime_score = ctx.get("regime_score", 7)

        if regime_score >= 12:
            status = "BULLISH"
            color = "#10b981"
            emoji = "🟢"
        elif regime_score >= 8:
            status = "NEUTRAL"
            color = "#f59e0b"
            emoji = "🟡"
        else:
            status = "BEARISH"
            color = "#ef4444"
            emoji = "🔴"

        return {
            "status": status, "color": color, "emoji": emoji,
            "vix": round(vix, 1) if vix else None,
            "vix_level": "Low" if vix and vix < 15 else "Moderate" if vix and vix < 20 else "High" if vix else "N/A",
            "nifty_trend": "Above 50 EMA" if nifty_bullish else "Below 50 EMA",
            "regime_score": regime_score,
        }
    except Exception as e:
        return {"status": "UNKNOWN", "color": "#64748b", "emoji": "⚪", "error": str(e)}


# ─── Sector Rotation ─────────────────────────────────────

@app.get("/api/screener/rotation")
async def sector_rotation():
    """Get sector rotation heatmap data."""
    try:
        from analysis.sector_rotation import get_sector_rotation
        data = await run_in_threadpool(get_sector_rotation)
        return data
    except Exception as e:
        print(f"❌ Sector rotation error: {e}")
        return {"sectors": [], "error": str(e)}


# ─── Why This Trade? ─────────────────────────────────────

@app.get("/api/stock/{symbol}/why")
async def why_this_trade(symbol: str):
    """Get AI-generated 'Why This Trade?' explanation."""
    try:
        ta_data = await run_in_threadpool(get_technical_analysis, symbol)
        if not ta_data:
            raise HTTPException(404, f"No data for {symbol}")

        from analysis.trade_explainer import explain_trade
        explanation = await run_in_threadpool(explain_trade, ta_data)

        return {
            "symbol": symbol,
            "score": ta_data.get("score"),
            "signal": ta_data.get("signal"),
            "explanation": explanation or "Explanation unavailable at this time.",
            "score_breakdown": ta_data.get("score_breakdown"),
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Why This Trade error: {e}")
        return {"symbol": symbol, "explanation": f"Error: {str(e)}"}


# ─── Position Sizing ─────────────────────────────────────

@app.get("/api/position/calculate")
async def calculate_position_size(
    entry: float, stop_loss: float,
    capital: float = 500000, risk_pct: float = 1.0
):
    """Calculate position size for a trade."""
    try:
        from analysis.position_sizing import calculate_position
        result = calculate_position(entry, stop_loss, capital, risk_pct)
        return result
    except Exception as e:
        return {"error": str(e)}


# ─── Accuracy Analyser ───────────────────────────────────

@app.get("/api/accuracy/stats")
async def accuracy_stats():
    """Get signal accuracy statistics."""
    try:
        from analysis.accuracy import get_accuracy_stats
        return await run_in_threadpool(get_accuracy_stats)
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/accuracy/update")
async def accuracy_update(background_tasks: BackgroundTasks):
    """Trigger outcome update for open signals (run after market close)."""
    try:
        from analysis.accuracy import update_signal_outcomes
        background_tasks.add_task(update_signal_outcomes)
        return {"status": "Accuracy update started in background"}
    except Exception as e:
        return {"error": str(e)}


# ─── Portfolio ───────────────────────────────────────────

class HoldingInput(BaseModel):
    symbol: str
    quantity: float
    buy_price: float
    buy_date: str = ""
    notes: str = ""
    asset_type: str = "stock"

@app.post("/api/portfolio/holdings")
async def add_holding_api(holding: HoldingInput):
    """Add a manual stock holding."""
    try:
        if not holding.buy_date:
            holding.buy_date = datetime.now().strftime("%Y-%m-%d")
        invested = round(holding.quantity * holding.buy_price, 2)
        db.add_holding(
            symbol=holding.symbol.upper(),
            name=holding.symbol.upper(),
            asset_type=holding.asset_type,
            quantity=holding.quantity,
            buy_price=holding.buy_price,
            buy_date=holding.buy_date,
            invested_amount=invested,
            notes=holding.notes,
        )
        return {"success": True, "message": f"Added {holding.symbol.upper()}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/api/portfolio/holdings/{holding_id}")
async def delete_holding_api(holding_id: int):
    """Remove a holding by ID."""
    try:
        conn = db.get_connection()
        cursor = db.get_cursor(conn)
        db.db_execute(cursor, "DELETE FROM holdings WHERE id = ?", (holding_id,))
        conn.commit()
        db.put_connection(conn)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/portfolio")
async def get_portfolio():
    """Get user's complete portfolio with current values."""
    try:
        holdings = db.get_holdings()
        mf_holdings = [h for h in holdings if h["asset_type"] == "mf"]
        stock_holdings = [h for h in holdings if h["asset_type"] == "stock"]

        # Calculate MF values
        mf_data = None
        if mf_holdings:
            mf_list = [{"scheme_code": h["scheme_code"], "invested": h["invested_amount"], "units": h["quantity"]} for h in mf_holdings]
            mf_data = await run_in_threadpool(get_mf_portfolio_value, mf_list)

        # Calculate stock values
        stock_data = []
        total_stock_invested = 0
        total_stock_current = 0
        for h in stock_holdings:
            ltp = await run_in_threadpool(get_ltp, h["symbol"])
            if ltp:
                current_val = h["quantity"] * ltp
                stock_data.append({
                    **h,
                    "ltp": ltp,
                    "current_value": round(current_val, 2),
                    "returns": round(current_val - h["invested_amount"], 2),
                    "returns_pct": round(((current_val - h["invested_amount"]) / h["invested_amount"]) * 100, 2) if h["invested_amount"] else 0,
                })
                total_stock_invested += h["invested_amount"]
                total_stock_current += current_val

        total_invested = (mf_data["total_invested"] if mf_data else 0) + total_stock_invested
        total_current = (mf_data["total_current"] if mf_data else 0) + total_stock_current

        return {
            "summary": {
                "total_invested": total_invested,
                "total_current": round(total_current, 2),
                "total_returns": round(total_current - total_invested, 2),
                "total_returns_pct": round(((total_current - total_invested) / total_invested) * 100, 2) if total_invested else 0,
            },
            "mutual_funds": mf_data,
            "stocks": stock_data,
        }
    except Exception as e:
        print(f"❌ Portfolio error: {traceback.format_exc()}")
        return {
            "summary": {"total_invested": 0, "total_current": 0, "total_returns": 0, "total_returns_pct": 0},
            "mutual_funds": None,
            "stocks": [],
            "error": str(e),
        }


class HoldingCreate(BaseModel):
    symbol: str
    name: str
    asset_type: str = "stock"
    exchange: str = "NSE"
    quantity: float = 0
    buy_price: float = 0
    buy_date: str = ""
    invested_amount: float = 0
    scheme_code: Optional[str] = None
    notes: Optional[str] = None


@app.post("/api/portfolio/add")
async def add_holding(h: HoldingCreate):
    """Add a new holding."""
    db.add_holding(h.symbol, h.name, h.asset_type, h.quantity, h.buy_price,
                   h.buy_date or datetime.now().strftime("%Y-%m-%d"),
                   h.invested_amount, h.exchange, h.scheme_code, h.notes)
    return {"status": "ok", "message": f"Added {h.name}"}


@app.delete("/api/portfolio/{holding_id}")
async def remove_holding(holding_id: int):
    """Remove a holding."""
    db.delete_holding(holding_id)
    return {"status": "ok"}


# ─── Mutual Funds ────────────────────────────────────────

@app.get("/api/mf/{scheme_code}")
async def mf_detail(scheme_code: str):
    """Get mutual fund details + historical NAV."""
    try:
        nav = await run_in_threadpool(get_mf_nav, scheme_code)
        history = await run_in_threadpool(get_mf_historical, scheme_code, days=365)
        if not nav:
            raise HTTPException(404, f"MF {scheme_code} not found")
        return {"current": nav, "history": history}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error fetching MF {scheme_code}: {str(e)}")


# ─── Signals ─────────────────────────────────────────────

@app.get("/api/signals")
async def get_signals():
    """Get all active signals."""
    try:
        return {"signals": db.get_active_signals()}
    except Exception as e:
        return {"signals": [], "error": str(e)}


@app.get("/api/signals/generate")
async def generate_signals():
    """Generate fresh signals from top screener picks."""
    try:
        results = await run_in_threadpool(screen_stocks, NIFTY_50_SYMBOLS, top_n=5)
        signals = []
        for r in results:
            if r["score"] >= 60:
                db.save_signal(
                    symbol=r["symbol"],
                    signal_type=r["signal"],
                    confidence=r["score"],
                    entry_price=r["entry"],
                    target_price=r["target"],
                    stop_loss=r["stop_loss"],
                    reasoning="; ".join(f"{s['indicator']}: {s['signal']}" for s in r["signals"]),
                )
                signals.append(r)
        return {"generated": len(signals), "signals": signals}
    except Exception as e:
        print(f"❌ Signal generation error: {e}")
        return {"generated": 0, "signals": [], "error": str(e)}


# ─── Paper Trading ───────────────────────────────────────

class TradeCreate(BaseModel):
    symbol: str
    trade_type: str
    quantity: float
    price: Optional[float] = None
    fees: float = 0
    notes: Optional[str] = None

@app.get("/api/paper/portfolio")
async def get_paper_portfolio():
    """Get paper trading positions and metrics."""
    try:
        return db.get_paper_portfolio()
    except Exception as e:
        return {"positions": [], "history": [], "metrics": {"realized_pnl": 0, "total_fees": 0, "net_realized_pnl": 0}, "error": str(e)}

@app.post("/api/paper/trade")
async def execute_paper_trade(t: TradeCreate):
    """Execute a simulated trade."""
    price = t.price or await run_in_threadpool(get_ltp, t.symbol)
    if not price:
        raise HTTPException(400, f"Could not get current price for {t.symbol}")
    
    # Calculate 0.1% fees if not provided
    fees = t.fees or (price * t.quantity * 0.001)
    
    db.add_paper_trade(t.symbol.upper(), t.trade_type.upper(), t.quantity, price, fees, t.notes)
    return {"status": "ok", "price": price, "fees": fees}

@app.get("/api/bot/alert")
@app.post("/api/bot/alert")
async def trigger_telegram_alert(background_tasks: BackgroundTasks):
    """Trigger the daily Telegram briefing in the background.
    Returns 200 immediately so cron-job.org doesn't timeout (30s limit).
    The actual briefing runs asynchronously and takes 1-2 minutes.
    """
    background_tasks.add_task(_run_daily_alert_sync)
    return {
        "status": "accepted",
        "message": "Agent Alpha briefing triggered. Telegram message will arrive in 1-2 minutes.",
        "timestamp": datetime.now().isoformat(),
    }


def _run_daily_alert_sync():
    """Run the daily alert synchronously in a background thread."""
    import asyncio
    from bot.daily_job import send_daily_alert
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(send_daily_alert())
        print(f"✅ Background alert completed: {result.get('status', 'unknown')}")
        return result
    except Exception as e:
        print(f"❌ Background alert failed: {e}")
    finally:
        loop.close()


@app.get("/api/debug")
async def debug_env():
    """Debug endpoint to check environment configuration on Render."""
    import requests as req
    
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    telegram_chat = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    
    results = {
        "gemini_key_exists": bool(gemini_key),
        "gemini_key_length": len(gemini_key),
        "gemini_key_preview": f"{gemini_key[:8]}...{gemini_key[-4:]}" if len(gemini_key) > 12 else "TOO_SHORT",
        "telegram_token_exists": bool(telegram_token),
        "telegram_token_length": len(telegram_token),
        "telegram_chat_id": telegram_chat,
    }
    
    # Test Gemini
    try:
        from google import genai
        client = genai.Client(api_key=gemini_key)
        resp = client.models.generate_content(model='gemini-2.0-flash', contents='Say: OK')
        results["gemini_status"] = "OK"
        results["gemini_response"] = resp.text[:100]
    except ImportError:
        results["gemini_status"] = "google-genai NOT INSTALLED"
    except Exception as e:
        results["gemini_status"] = f"FAILED: {str(e)[:200]}"
    
    # Test Telegram
    if telegram_token and telegram_chat:
        try:
            url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
            payload = {"chat_id": telegram_chat, "text": f"🔧 Debug ping at {datetime.now().isoformat()}"}
            r = req.post(url, json=payload, timeout=10)
            results["telegram_status"] = f"HTTP {r.status_code}"
            if r.status_code != 200:
                results["telegram_error"] = r.text[:200]
        except Exception as e:
            results["telegram_status"] = f"FAILED: {str(e)}"
    else:
        results["telegram_status"] = "MISSING CREDENTIALS"
    
    return results


# ─── Health ──────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "name": "Agent Alpha",
        "version": "2.0.0",
        "db_connected": bool(db.DATABASE_URL and db.pool),
    }

@app.on_event("startup")
async def start_keep_alive():
    """Self-ping to prevent Render from sleeping on free tier."""
    import httpx
    import asyncio
    
    async def ping_self():
        url = os.getenv("RENDER_EXTERNAL_URL")
        if not url:
            return
        # Render gives host without protocol
        if not url.startswith("http"):
            url = f"https://{url}"
        async with httpx.AsyncClient() as client:
            while True:
                try:
                    await client.get(f"{url}/api/health", timeout=10)
                    print("🏓 Keep-alive ping sent")
                except Exception:
                    pass
                await asyncio.sleep(600) # Every 10 mins
    
    asyncio.create_task(ping_self())


if __name__ == "__main__":
    # startCommand: gunicorn backend.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 120
    import uvicorn
    from config import HOST, PORT
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
