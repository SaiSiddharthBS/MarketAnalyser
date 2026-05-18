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

# Task 15: Structured Logging
from config.logging import setup_logging, RequestTimingMiddleware
logger = setup_logging()

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


# ─── Task 13: Standardized Error Response ─────────────────────

class ErrorResponse(BaseModel):
    error: bool = True
    message: str
    code: str

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Catch all unhandled exceptions and return a consistent JSON structure."""
    logger.error(f"Unhandled exception on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": True, "message": str(exc), "code": "INTERNAL_ERROR"}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Standardize HTTPException responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": True, "message": exc.detail, "code": f"HTTP_{exc.status_code}"}
    )

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Task 15: Request timing middleware
app.add_middleware(RequestTimingMiddleware)

# Serve frontend static files
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.on_event("startup")
async def startup():
    # Task 14: Print validated config summary
    try:
        from config.settings import settings
        settings.print_startup_summary()
    except Exception as se:
        logger.warning("Settings validation: %s", se)
    try:
        db.init_db()
        _seed_portfolio()
        
        # Verify any pending intraday predictions from previous days
        # Do this in the background so it doesn't block server startup
        import asyncio
        from starlette.concurrency import run_in_threadpool
        
        async def background_verification():
            try:
                from analysis.accuracy import verify_intraday_predictions, resolve_pending_signals
                await run_in_threadpool(verify_intraday_predictions)
                # Task 7: Signal Outcome Resolver
                await run_in_threadpool(resolve_pending_signals)
            except Exception as ve:
                logger.warning("Prediction verification on startup failed: %s", ve)
                
        asyncio.create_task(background_verification())
    except Exception as e:
        logger.warning("Startup error (non-fatal): %s", e)


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
            logger.info("Pre-loaded user MF holdings")
    except Exception as e:
        logger.warning("Seed error: %s", e)


# ─── Frontend Routes ─────────────────────────────────────

@app.get("/")
async def serve_frontend():
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"message": "MarketPulse API is running. Frontend not found."}


# ─── Cache Management ──────────────────────────────────────

@app.get("/api/cache/stats")
async def cache_stats():
    from data.cache import cache
    return cache.get_stats()


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
            logger.warning("Market overview fetch timed out!")
            indices, news, sentiment = Exception("Timeout"), Exception("Timeout"), Exception("Timeout")

        # Handle partial failures gracefully
        if isinstance(indices, Exception):
            logger.warning("Indices fetch failed: %s", indices)
            indices = {}
        if isinstance(news, Exception):
            logger.warning("News fetch failed: %s", news)
            news = []
        if isinstance(sentiment, Exception):
            logger.warning("Sentiment fetch failed: %s", sentiment)
            sentiment = {"score": 0, "label": "Unavailable", "positive_pct": 0, "negative_pct": 0}

        from data.stock_fetcher import get_market_status
        return {
            "timestamp": datetime.now().isoformat(),
            "market_status": get_market_status(),
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
        logger.error("Market overview error: %s", traceback.format_exc())
        from data.stock_fetcher import get_market_status
        return {
            "timestamp": datetime.now().isoformat(),
            "market_status": get_market_status() if 'get_market_status' in locals() else "UNKNOWN",
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

# Task 25: Lightweight Price Endpoint for Alerts
@app.get("/api/price/{symbol}")
async def get_current_price(symbol: str):
    """Fetch only the latest price and volume for a symbol (cached)."""
    try:
        from data.stock_fetcher import get_stock_data
        data = await run_in_threadpool(get_stock_data, symbol, period="5d")
        if not data:
            raise HTTPException(404, "Data unavailable")
        latest = data[-1]
        return {
            "symbol": symbol,
            "price": latest["Close"],
            "volume": latest["Volume"],
            "timestamp": latest["Date"]
        }
    except Exception as e:
        raise HTTPException(500, str(e))

# Task 22: F&O Options Chain Endpoint
@app.get("/api/options/{symbol}")
async def get_options_data(symbol: str):
    """Get basic F&O options data (PCR, Max Pain) for a symbol."""
    try:
        from data.options_fetcher import fetch_options_chain, calculate_pcr, calculate_max_pain
        opt_data = await run_in_threadpool(fetch_options_chain, symbol)
        if not opt_data:
            raise HTTPException(404, f"Options data unavailable for {symbol}")
        
        data = opt_data.get("data", [])
        underlying = opt_data.get("underlying_value", 0)
        pcr_stats = calculate_pcr(data)
        max_pain = calculate_max_pain(data, underlying_price=underlying)
        
        return {
            "symbol": symbol,
            "pcr": pcr_stats,
            "max_pain": max_pain,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Options API Error for {symbol}: {e}")
        raise HTTPException(500, f"Error fetching options: {str(e)}")

# ─── Stock Analysis ──────────────────────────────────────

def _find_sector_for_symbol(symbol):
    """Find which actual sector a stock belongs to and return its yahoo index."""
    for key, seg in SECTOR_INDICES.items():
        if key == "NIFTY_50":
            continue
        if symbol.upper() in seg["symbols"]:
            return seg.get("yahoo_index", "^NSEI")
    return "^NSEI"

def _compute_retroactive_verification(symbol: str, ta_result) -> dict:
    """
    Compute a real-time 'Yesterday Prediction vs Today Reality' using historical data.
    Uses day T-2's close + ATR to predict day T-1's range, then grades against T-1's actual OHLC.
    This ensures the verification section is NEVER empty.
    """
    try:
        import pandas as pd
        import ta as ta_lib

        data = get_stock_data(symbol, period="10d", interval="1d")
        if not data or len(data) < 3:
            return None

        df = pd.DataFrame(data)
        if len(df) < 3:
            return None

        # Yesterday's close = prediction base (what we would have predicted yesterday evening)
        yesterday = df.iloc[-2]
        # Today's completed OHLC = the reality we grade against
        today = df.iloc[-1]

        prev_close = float(yesterday["Close"])

        # Compute ATR using data up to yesterday for the prediction
        atr_series = ta_lib.volatility.AverageTrueRange(
            df["High"], df["Low"], df["Close"], window=min(14, len(df) - 1)
        ).average_true_range()
        atr_val = float(atr_series.iloc[-2]) if len(atr_series) >= 2 and pd.notna(atr_series.iloc[-2]) else prev_close * 0.02

        pred_high = round(prev_close + atr_val, 2)
        pred_low = round(prev_close - atr_val, 2)

        # Determine predicted direction from the technical result
        if ta_result and not isinstance(ta_result, Exception):
            sig = ta_result.get("signal", "NEUTRAL")
            if sig in ["BUY", "STRONG_BUY"]:
                pred_direction = "Bullish"
            elif sig in ["SELL", "STRONG_SELL"]:
                pred_direction = "Bearish"
            else:
                pred_direction = "Neutral"
        else:
            pred_direction = "Neutral"

        actual_open = round(float(today["Open"]), 2)
        actual_high = round(float(today["High"]), 2)
        actual_low = round(float(today["Low"]), 2)
        actual_close = round(float(today["Close"]), 2)

        # Grade it
        status_parts = []
        if actual_high <= pred_high and actual_low >= pred_low:
            status_parts.append("✅ Within Range")
        else:
            status_parts.append("❌ Range Breached")

        actual_dir = "Bullish" if actual_close > actual_open else ("Bearish" if actual_close < actual_open else "Neutral")
        if pred_direction == actual_dir:
            status_parts.append("✅ Direction Hit")
        else:
            status_parts.append("❌ Direction Missed")

        return {
            "pred_high": pred_high,
            "pred_low": pred_low,
            "pred_direction": pred_direction,
            "actual_open": actual_open,
            "actual_high": actual_high,
            "actual_low": actual_low,
            "actual_close": actual_close,
            "status": " | ".join(status_parts),
            "target_date": str(today.get("Date", "Today")),
        }
    except Exception as e:
        logger.warning("Retroactive verification failed for %s: %s", symbol, e)
        return None


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

        # Always compute fresh verification from live data (DB records can be stale)
        verification = await run_in_threadpool(
            _compute_retroactive_verification, symbol, ta_result
        )

        return {
            "info": info if not isinstance(info, Exception) else None,
            "technical": ta_result if not isinstance(ta_result, Exception) else None,
            "news": (news[:5] if isinstance(news, list) else []),
            "recent_verification": verification,
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

@app.get("/api/regime")
async def get_regime():
    """Get the current smoothed market regime."""
    try:
        from analysis.regime import get_smoothed_market_regime
        regime_data = await run_in_threadpool(get_smoothed_market_regime)
        return regime_data
    except Exception as e:
        raise HTTPException(500, f"Error calculating regime: {str(e)}")

@app.get("/api/screener/segments")
async def screener_segments():
    """List all available screener segments."""
    return [
        {"key": k, "name": v["name"], "count": len(v["symbols"])}
        for k, v in SECTOR_INDICES.items()
    ]


@app.get("/api/screener/top")
async def screener_top(n: int = 10, segment: str = "NIFTY_50", direction: str = "LONG"):
    """Get top N stocks by technical score from a segment."""
    try:
        if segment == "ALL_SECTORS":
            # Scan top 2 from each sector, merge and rank
            all_results = []
            import time as _time
            start_ts = _time.time()
            MAX_SCREENER_SECONDS = 180  # 3 min hard cap — return partial results after this
            
            for seg_key, seg_data in SECTOR_INDICES.items():
                # If we've been running too long, return what we have
                if _time.time() - start_ts > MAX_SCREENER_SECONDS:
                    logger.warning("Screener hit 3-min cap after %d sectors. Returning partial results.", len(all_results))
                    break
                try:
                    # Upgrade 12: Permanent Exclusion List
                    EXCLUSIONS = {"LIQUIDBEES", "LIQUIDCASE", "LIQUIDETF", "LICNETFGSC"}
                    symbols = [s for s in seg_data["symbols"] if s not in EXCLUSIONS][:8]  # 8 per sector for speed
                    yahoo_idx = seg_data.get("yahoo_index", "^NSEI")
                    results = await run_in_threadpool(screen_stocks, symbols, top_n=2, sector_yahoo_index=yahoo_idx, direction=direction.upper())
                    for r in results:
                        r["sector_name"] = seg_data["name"]
                    all_results.extend(results)
                except Exception as seg_err:
                    logger.warning("Skipping %s: %s", seg_key, seg_err)
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
            elapsed = round(_time.time() - start_ts, 1)
            return {
                "segment": "ALL_SECTORS",
                "segment_name": f"🔥 All Sectors — Top {direction.upper()} Picks ({elapsed}s)",
                "count": len(all_results),
                "stocks": all_results,
                "signal_labels": SIGNAL_LABELS,
            }

        seg_data = SECTOR_INDICES.get(segment)
        if not seg_data:
            return {"count": 0, "stocks": [], "error": f"Unknown segment: {segment}"}

        # Upgrade 12: Permanent Exclusion List
        EXCLUSIONS = {"LIQUIDBEES", "LIQUIDCASE", "LIQUIDETF", "LICNETFGSC"}
        symbols = [s for s in seg_data["symbols"] if s not in EXCLUSIONS]
        yahoo_index = seg_data.get("yahoo_index", "^NSEI")
        results = await run_in_threadpool(
            screen_stocks, symbols, top_n=n, sector_yahoo_index=yahoo_index, direction=direction.upper()
        )

        # Log signals for accuracy tracking (Day 1)
        try:
            import database as db
            db.log_screener_signals(results, segment=segment)
        except Exception as log_err:
            logger.warning("Signal logging failed: %s", log_err)

        error_msg = "🛡️ No stocks met the strict institutional criteria for the current market regime. Capital preservation is active."
        if direction.upper() == "SHORT":
            error_msg = "📉 No short setups met the criteria. Markets might be bouncing."
            
        return {
            "segment": segment,
            "segment_name": seg_data["name"] + f" ({direction.upper()}S)",
            "count": len(results),
            "stocks": results,
            "signal_labels": SIGNAL_LABELS,
            "error": error_msg if len(results) == 0 else None
        }
    except Exception as e:
        logger.error("Screener error: %s", e)
        return {"count": 0, "stocks": [], "error": str(e)}


# ─── Market Regime ───────────────────────────────────────

@app.get("/api/market/regime")
async def market_regime():
    """Get current smoothed market regime for the global bar."""
    try:
        from analysis.regime import get_smoothed_market_regime
        regime_data = await run_in_threadpool(get_smoothed_market_regime)
        return regime_data
    except Exception as e:
        return {"status": "UNKNOWN", "color": "#6b7280", "emoji": "⚪", "error": str(e)}


# ─── Sector Rotation ─────────────────────────────────────

@app.get("/api/screener/rotation")
async def sector_rotation():
    """Get sector rotation heatmap data."""
    try:
        from analysis.sector_rotation import get_sector_rotation
        data = await run_in_threadpool(get_sector_rotation)
        return data
    except Exception as e:
        logger.error("Sector rotation error: %s", e)
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
        logger.error("Why This Trade error: %s", e)
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
        raise HTTPException(status_code=400, detail=f"Position calculation failed: {e}")


# ─── Accuracy Analyser ───────────────────────────────────

@app.get("/api/accuracy/walk-forward")
async def walk_forward_endpoint(symbol: str = "RELIANCE", folds: int = 5):
    """Run Walk-Forward Validation on historical data."""
    try:
        from data.stock_fetcher import get_stock_data
        from analysis.walk_forward import run_walk_forward_validation
        import pandas as pd
        
        # We need lots of data for walk-forward
        data = get_stock_data(symbol, period="5y", interval="1d")
        if not data:
            raise HTTPException(status_code=404, detail=f"Could not fetch data for {symbol}")
            
        df = pd.DataFrame(data)
        result = await run_in_threadpool(run_walk_forward_validation, df, folds=folds)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Walk-forward validation failed: {e}")

@app.get("/api/accuracy/stats")
async def accuracy_stats():
    """Get signal accuracy statistics."""
    try:
        from analysis.accuracy import get_accuracy_stats
        return await run_in_threadpool(get_accuracy_stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Accuracy stats unavailable: {e}")


@app.get("/api/accuracy/update")
async def accuracy_update(background_tasks: BackgroundTasks):
    """Trigger outcome update for open signals (run after market close)."""
    try:
        from analysis.accuracy import resolve_pending_signals
        background_tasks.add_task(resolve_pending_signals)
        return {"status": "Accuracy update started in background"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Accuracy update failed: {e}")


@app.get("/api/championship")
async def get_championship_leaderboard():
    """Phase 3: Championship Leaderboard"""
    try:
        from arena.championship import get_leaderboard
        return get_leaderboard()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Leaderboard error: {e}")


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

class PaperTradeInput(BaseModel):
    symbol: str
    entry_price: float
    target_price: float = None
    stop_loss: float = None
    qty: int
    notes: str = ""

@app.post("/api/paper_trades")
async def add_paper_trade(trade: PaperTradeInput):
    """Upgrade 13: Create a paper trade."""
    try:
        query = """INSERT INTO paper_trades 
                   (symbol, entry_price, entry_date, target_price, stop_loss, qty, notes) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)"""
        db.db_execute(query, (
            trade.symbol.upper(), trade.entry_price, datetime.now().isoformat(),
            trade.target_price, trade.stop_loss, trade.qty, trade.notes
        ))
        return {"success": True, "message": f"Paper trade started for {trade.symbol}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/paper_trades")
async def get_paper_trades():
    """Upgrade 13: Get all paper trades."""
    try:
        query = "SELECT * FROM paper_trades ORDER BY created_at DESC"
        trades = db.db_execute(query)
        # Convert sqlite3.Row objects to dicts
        return [dict(t) for t in trades] if trades else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Paper trades unavailable: {e}")

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
        logger.error("Portfolio error: %s", traceback.format_exc())
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
        logger.error("Signal generation error: %s", e)
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

class NewsAlertPayload(BaseModel):
    type: str
    category: str
    headline: str
    link: str

@app.post("/api/bot/alert/news")
async def trigger_news_alert(payload: NewsAlertPayload, background_tasks: BackgroundTasks):
    """Phase 4: Sentinel News Triage Alert"""
    try:
        from bot.telegram_bot import send_urgent_news_alert
        background_tasks.add_task(send_urgent_news_alert, payload.category, payload.headline, payload.link)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"News alert failed: {e}")
        return {"status": "error", "message": str(e)}

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
        logger.info("Background alert completed: %s", result.get('status', 'unknown'))
        return result
    except Exception as e:
        logger.error("Background alert failed: %s", e)
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

# ─── Arena (Paper Trading) ───────────────────────────────

@app.get("/api/arena/portfolio")
async def get_arena_portfolio():
    from arena.paper_trading import get_latest_portfolio
    return get_latest_portfolio()

@app.get("/api/arena/trades")
async def get_arena_trades():
    import database as db
    open_trades = db.db_execute("SELECT * FROM paper_trades WHERE status = 'OPEN' ORDER BY entry_date DESC")
    closed_trades = db.db_execute("SELECT * FROM paper_trades WHERE status != 'OPEN' ORDER BY exit_date DESC")
    return {"open": open_trades, "closed": closed_trades}

@app.get("/api/arena/equity-curve")
async def get_arena_equity_curve():
    import database as db
    history = db.db_execute("SELECT date, total_equity, benchmark_nifty_return_pct FROM paper_portfolio ORDER BY date ASC")
    return {"history": history}

@app.get("/api/arena/stats")
async def get_arena_stats():
    import database as db
    res = db.db_execute("SELECT * FROM paper_monthly_stats ORDER BY month DESC")
    
    total_trades_res = db.db_execute("SELECT COUNT(*) as count FROM paper_trades WHERE status != 'OPEN'")
    total_trades = total_trades_res[0]["count"] if total_trades_res else 0
    
    wins_res = db.db_execute("SELECT COUNT(*) as count FROM paper_trades WHERE status = 'CLOSED_WIN'")
    wins = wins_res[0]["count"] if wins_res else 0
    
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0.0
    
    return {
        "monthly_stats": res,
        "overall": {
            "total_trades": total_trades,
            "wins": wins,
            "win_rate": win_rate
        }
    }

@app.post("/api/arena/execute")
async def trigger_arena_execute(background_tasks: BackgroundTasks):
    from arena.paper_trading import execute_daily_arena
    background_tasks.add_task(execute_daily_arena)
    return {"status": "Execution triggered"}


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
                    logger.debug("Keep-alive ping sent")
                except Exception:
                    pass
                await asyncio.sleep(600) # Every 10 mins
    
    asyncio.create_task(ping_self())


if __name__ == "__main__":
    # startCommand: gunicorn backend.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 120
    import uvicorn
    from config import HOST, PORT
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
