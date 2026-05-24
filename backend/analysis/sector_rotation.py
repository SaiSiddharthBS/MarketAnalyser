"""
MarketPulse — Sector Command Center
Evaluates all sectors, classifies each by relative strength vs Nifty 50,
and detects rotation between cyclical and defensive sectors.
"""
import ta
import threading
from data.stock_fetcher import download_ohlcv
from config import SECTOR_INDICES
from analysis.relative_strength import get_relative_strength

_sector_cache = {}
_cache_lock = threading.Lock()

def get_sector_rotation():
    """Analyse all sectors and return rotation heatmap data."""
    # Using locking to prevent duplicate calculations in parallel requests
    global _sector_cache
    with _cache_lock:
        if _sector_cache:
            return _sector_cache
            
    # Fetch Nifty 50 benchmark data (need 6mo for full analysis)
    nifty_df = download_ohlcv("^NSEI", period="1y", interval="1d")
    if nifty_df is None or nifty_df.empty or len(nifty_df) < 126:
        return {"error": "Could not fetch Nifty 50 data", "sectors": []}

    nifty_1w = _pct_return(nifty_df, 5)
    nifty_1m = _pct_return(nifty_df, 21)
    nifty_3m = _pct_return(nifty_df, 63)
    nifty_6m = _pct_return(nifty_df, 126)

    results = []

    # Only evaluate actual sector indices
    sector_keys = [
        "NIFTY_50", "NIFTY_BANK", "NIFTY_IT", "NIFTY_PHARMA", "NIFTY_AUTO",
        "NIFTY_METAL", "NIFTY_FMCG", "NIFTY_ENERGY", "NIFTY_INFRA",
        "NIFTY_PSU_BANK", "NIFTY_REALTY",
    ]

    for key in sector_keys:
        seg = SECTOR_INDICES.get(key)
        if not seg:
            continue

        try:
            yahoo_idx = seg.get("yahoo_index", "^NSEI")
            sector_df = download_ohlcv(yahoo_idx, period="1y", interval="1d")

            if sector_df is None or sector_df.empty or len(sector_df) < 126:
                results.append(_fallback_sector(key, seg["name"]))
                continue

            # Sector returns
            s_1w = _pct_return(sector_df, 5)
            s_1m = _pct_return(sector_df, 21)
            s_3m = _pct_return(sector_df, 63)
            s_6m = _pct_return(sector_df, 126)

            # Relative strength vs Nifty
            rel_1w = s_1w - nifty_1w
            rel_1m = s_1m - nifty_1m
            rel_3m = s_3m - nifty_3m
            rel_6m = s_6m - nifty_6m
            
            # Composite RS Score (weighted towards medium term)
            relative_strength = (rel_1w * 0.15) + (rel_1m * 0.35) + (rel_3m * 0.35) + (rel_6m * 0.15)

            # Breadth: % of sector stocks above their 50 EMA
            breadth = _calc_breadth(seg["symbols"])

            # RVOL for sector index
            rvol = _calc_rvol(sector_df)

            # Find Best in Class Stock
            best_stock = "N/A"
            best_rs = -1000
            for sym in seg["symbols"]:
                stock_rs = get_relative_strength(sym)
                if stock_rs["rs_percentile"] > best_rs:
                    best_rs = stock_rs["rs_percentile"]
                    best_stock = sym

            # Composite score for classification
            composite = (relative_strength * 3) + (breadth - 50) * 0.1 + (rvol - 1) * 5

            # Classify
            if composite > 5:
                classification = "🔥 Strong"
                color = "#00e676"
            elif composite > 1.5:
                classification = "↗ Improving"
                color = "#69f0ae"
            elif composite > -1.5:
                classification = "→ Neutral"
                color = "#ffd740"
            elif composite > -5:
                classification = "↘ Weakening"
                color = "#ff9800"
            else:
                classification = "❄ Avoid"
                color = "#ff5252"

            results.append({
                "key": key,
                "name": seg["name"],
                "stock_count": len(seg["symbols"]),
                "classification": classification,
                "color": color,
                "relative_strength": round(relative_strength, 2),
                "returns": {
                    "1w": round(s_1w, 2),
                    "1m": round(s_1m, 2),
                    "3m": round(s_3m, 2),
                    "6m": round(s_6m, 2),
                },
                "nifty_returns": {
                    "1w": round(nifty_1w, 2),
                    "1m": round(nifty_1m, 2),
                    "3m": round(nifty_3m, 2),
                    "6m": round(nifty_6m, 2),
                },
                "breadth": round(breadth, 1),
                "rvol": round(rvol, 2),
                "composite_score": round(composite, 2),
                "best_in_class": best_stock,
                "best_in_class_rs": best_rs
            })

        except Exception as e:
            print(f"⚠️ Sector rotation error for {key}: {e}")
            results.append(_fallback_sector(key, seg["name"]))

    # Sort by composite score (strongest first)
    results.sort(key=lambda x: x.get("composite_score", 0), reverse=True)
    
    with _cache_lock:
        _sector_cache = {"sectors": results}
    
    return _sector_cache


def get_sector_for_symbol(symbol: str) -> dict:
    """Helper to get sector momentum for a specific symbol."""
    rotation_data = get_sector_rotation()
    
    for sector in rotation_data.get("sectors", []):
        seg = SECTOR_INDICES.get(sector["key"], {})
        if symbol in seg.get("symbols", []):
            return {
                "sector_name": sector["name"],
                "classification": sector["classification"],
                "composite_score": sector["composite_score"],
                "is_best_in_class": symbol == sector.get("best_in_class")
            }
            
    return {
        "sector_name": "UNKNOWN",
        "classification": "→ Neutral",
        "composite_score": 0.0,
        "is_best_in_class": False
    }

def _pct_return(df, days):
    """Calculate % return over N days."""
    if len(df) < days:
        return 0.0
    return (float(df["Close"].iloc[-1]) / float(df["Close"].iloc[-days]) - 1) * 100


def _calc_breadth(symbols, exchange="NS"):
    """Calculate % of stocks above their 50 EMA."""
    above = 0
    total = 0
    for sym in symbols[:15]:  # Limit to 15 to keep it fast
        try:
            ticker = f"{sym}.{exchange}"
            df = download_ohlcv(ticker, period="3mo", interval="1d")
            if df is not None and not df.empty and len(df) >= 50:
                ema50 = ta.trend.EMAIndicator(close=df["Close"], window=50).ema_indicator()
                if float(df["Close"].iloc[-1]) > float(ema50.iloc[-1]):
                    above += 1
                total += 1
        except Exception:
            pass
    return (above / total * 100) if total > 0 else 50.0


def _calc_rvol(df):
    """Calculate relative volume (current vs 20-day avg)."""
    if df is None or df.empty or len(df) < 20:
        return 1.0
    current_vol = float(df["Volume"].iloc[-1])
    avg_vol = float(df["Volume"].tail(20).mean())
    return round(current_vol / avg_vol, 2) if avg_vol > 0 else 1.0


def _fallback_sector(key, name):
    """Return a neutral fallback when data is unavailable."""
    return {
        "key": key,
        "name": name,
        "stock_count": 0,
        "classification": "→ Neutral",
        "color": "#ffd740",
        "relative_strength": 0,
        "returns": {"1w": 0, "1m": 0, "3m": 0, "6m": 0},
        "nifty_returns": {"1w": 0, "1m": 0, "3m": 0, "6m": 0},
        "breadth": 50,
        "rvol": 1.0,
        "composite_score": 0,
        "best_in_class": "N/A",
        "best_in_class_rs": 0
    }
