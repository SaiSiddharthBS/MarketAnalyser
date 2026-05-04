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
from config import NIFTY_50_SYMBOLS, USER_MF_HOLDINGS

app = FastAPI(title="MarketPulse - Agent Alpha", version="2.0.0")

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

@app.get("/api/stock/{symbol}")
async def stock_detail(symbol: str):
    """Get full analysis for a stock."""
    try:
        info_task = run_in_threadpool(get_stock_info, symbol)
        ta_task = run_in_threadpool(get_technical_analysis, symbol)
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
        data = await run_in_threadpool(get_stock_data, symbol, period=period)
        if not data:
            raise HTTPException(404, f"No data for {symbol}")
        return {"symbol": symbol, "period": period, "data": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error fetching chart for {symbol}: {str(e)}")


# ─── Screener ────────────────────────────────────────────

@app.get("/api/screener/top")
async def screener_top(n: int = 10):
    """Get top N stocks by technical score from Nifty 50."""
    try:
        results = await run_in_threadpool(screen_stocks, NIFTY_50_SYMBOLS, top_n=n)
        return {"count": len(results), "stocks": results}
    except Exception as e:
        print(f"❌ Screener error: {e}")
        return {"count": 0, "stocks": [], "error": str(e)}


# ─── Portfolio ───────────────────────────────────────────

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
    """Manually trigger the daily Telegram briefing as a background task."""
    from bot.daily_job import send_daily_alert
    
    # Define a sync wrapper for the async job since background tasks can handle async, but sometimes need wrapper
    async def run_job():
        try:
            await send_daily_alert()
        except Exception as e:
            print(f"❌ Background Telegram alert error: {e}")
            
    background_tasks.add_task(run_job)
    return {"status": "queued", "message": "Daily alert triggered in background."}


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
