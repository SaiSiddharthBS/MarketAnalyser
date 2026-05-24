"""
Agent Alpha v3.0 — Relative Strength Ranker (Jegadeesh & Titman 1993)
====================================================================
Ranks the Nifty 50 universe by pure price momentum over multiple timeframes.
Composite RS = 40% (3M) + 35% (6M) + 25% (12M)
Outputs a percentile ranking (0 to 100) for each stock.
"""
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
import threading
from config import NIFTY_50_SYMBOLS
from data.stock_fetcher import download_ohlcv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory cache for RS scores to avoid re-fetching 50 stocks for every query
_rs_cache = {}
_cache_timestamp = None
_cache_lock = threading.Lock()

def _calculate_stock_returns(symbol: str) -> dict:
    """Calculate 3M, 6M, and 12M returns for a specific stock."""
    # We need slightly more than 1Y of data to be safe (252 trading days = 1 year)
    df = download_ohlcv(f"{symbol}.NS", period="2y", interval="1d")
    
    if df is None or len(df) < 252:
        return {"3m": 0.0, "6m": 0.0, "12m": 0.0, "valid": False}
        
    try:
        current_close = float(df["Close"].iloc[-1])
        
        # Approximate trading days: 3M = ~63 days, 6M = ~126 days, 12M = ~252 days
        close_3m = float(df["Close"].iloc[-min(63, len(df))])
        close_6m = float(df["Close"].iloc[-min(126, len(df))])
        close_12m = float(df["Close"].iloc[-min(252, len(df))])
        
        ret_3m = (current_close / close_3m) - 1
        ret_6m = (current_close / close_6m) - 1
        ret_12m = (current_close / close_12m) - 1
        
        return {
            "3m": ret_3m,
            "6m": ret_6m,
            "12m": ret_12m,
            "valid": True
        }
    except Exception as e:
        logger.error(f"Error calculating returns for {symbol}: {e}")
        return {"3m": 0.0, "6m": 0.0, "12m": 0.0, "valid": False}

def _build_rs_rankings():
    """Build the RS rankings for all NIFTY 50 stocks."""
    global _rs_cache, _cache_timestamp
    
    logger.info("Building Relative Strength Matrix for NIFTY 50...")
    raw_scores = {}
    
    for symbol in NIFTY_50_SYMBOLS:
        returns = _calculate_stock_returns(symbol)
        if returns["valid"]:
            # Composite RS Score = 40% (3M) + 35% (6M) + 25% (12M)
            composite_score = (returns["3m"] * 0.40) + (returns["6m"] * 0.35) + (returns["12m"] * 0.25)
            raw_scores[symbol] = composite_score
            
    if not raw_scores:
        return
        
    # Convert to percentiles (0 to 100)
    scores_series = pd.Series(raw_scores)
    percentiles = scores_series.rank(pct=True) * 100
    
    new_cache = {}
    for symbol, pct in percentiles.items():
        decile = int(pct // 10) + 1  # 1 to 10 (10 being top)
        if decile > 10: decile = 10
        
        classification = "NEUTRAL"
        if pct >= 90:
            classification = "TOP_DECILE (Strong Buy Bias)"
        elif pct >= 80:
            classification = "STRONG"
        elif pct <= 10:
            classification = "BOTTOM_DECILE (Avoid/Short Bias)"
        elif pct <= 20:
            classification = "WEAK"
            
        new_cache[symbol] = {
            "rs_percentile": round(pct, 2),
            "rs_raw_score": round(raw_scores[symbol], 4),
            "rs_decile": decile,
            "classification": classification
        }
        
    with _cache_lock:
        _rs_cache = new_cache
        _cache_timestamp = datetime.now()
        logger.info(f"RS Matrix built successfully. {_cache_timestamp}")

def get_relative_strength(symbol: str) -> dict:
    """
    Get the relative strength data for a specific symbol.
    Uses caching to avoid recalculating the matrix.
    """
    global _rs_cache, _cache_timestamp
    
    # Rebuild cache if empty or older than 12 hours
    needs_rebuild = False
    with _cache_lock:
        if not _rs_cache or _cache_timestamp is None:
            needs_rebuild = True
        elif (datetime.now() - _cache_timestamp).total_seconds() > (12 * 3600):
            needs_rebuild = True
            
    if needs_rebuild:
        _build_rs_rankings()
        
    with _cache_lock:
        return _rs_cache.get(symbol, {
            "rs_percentile": 50.0,
            "rs_raw_score": 0.0,
            "rs_decile": 5,
            "classification": "UNKNOWN (Not in Universe)"
        })

if __name__ == "__main__":
    print("Testing RS Matrix Build...")
    _build_rs_rankings()
    for sym in ["RELIANCE", "TCS", "HDFCBANK", "INFY"]:
        rs = get_relative_strength(sym)
        print(f"{sym}: {rs}")
