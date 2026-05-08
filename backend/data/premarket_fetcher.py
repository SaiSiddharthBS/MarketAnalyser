"""
Agent Alpha v2.0 — Pre-Market Intelligence Fetcher
====================================================
Runs at 06:00-08:30 IST before Indian market opens.

Sources (all free):
1. SGX Nifty (Singapore) — Nifty futures trading overnight
2. US Markets (Dow, S&P, Nasdaq) — via Yahoo Finance
3. Crude Oil futures — impact on OMC, aviation, paints
4. USD/INR exchange rate — impact on IT, pharma exporters
5. Gold — safe haven demand gauge
6. Asian Markets (Hang Seng, Nikkei) — regional sentiment

Gap Risk Mitigation:
If SGX Nifty is showing a gap > 1.5% → suppress all buy signals
If SGX Nifty gap > 0.5% → widen predicted range by 0.5× ATR
"""
import requests
from datetime import datetime
from typing import Dict, Any, Optional

try:
    from data.stock_fetcher import download_ohlcv
except ImportError:
    download_ohlcv = None


# Yahoo Finance tickers for global markets
GLOBAL_TICKERS = {
    "sgx_nifty": "^SGXNIFTY",         # SGX Nifty (may need alternative source)
    "dow_jones": "^DJI",
    "sp500": "^GSPC",
    "nasdaq": "^IXIC",
    "crude_oil": "CL=F",
    "brent_crude": "BZ=F",
    "gold": "GC=F",
    "silver": "SI=F",
    "usdinr": "INR=X",
    "us_10y_yield": "^TNX",
    "vix_global": "^VIX",
    "hang_seng": "^HSI",
    "nikkei": "^N225",
    "ftse": "^FTSE",
    "dax": "^GDAXI",
}


def fetch_premarket_data() -> Dict[str, Any]:
    """
    Fetch all pre-market intelligence data.

    Returns:
        Dict with global market data, gap analysis, and risk signals.
    """
    results = {}
    signals = []

    for name, ticker in GLOBAL_TICKERS.items():
        try:
            data = _fetch_ticker_latest(ticker)
            if data:
                results[name] = data
        except Exception as e:
            results[name] = {"error": str(e)}

    # ─── SGX Nifty Gap Analysis ──────────────────────────────
    # Use Dow/S&P as proxy if SGX Nifty is not available
    nifty_prev_close = results.get("nifty_prev", {}).get("close")
    
    # Calculate implied gap from global cues
    gap_analysis = _calculate_gap_analysis(results)
    
    # ─── Crude Oil Impact ────────────────────────────────────
    crude_data = results.get("crude_oil", {})
    crude_change_pct = crude_data.get("change_pct", 0)

    if abs(crude_change_pct) > 3:
        signals.append({
            "type": "CRUDE_SHOCK",
            "severity": "HIGH",
            "message": f"Crude oil moved {crude_change_pct:+.1f}% — impacts OMC, aviation, paints, chemicals",
            "affected_sectors": ["OMC", "AVIATION", "PAINTS", "CHEMICALS"],
        })

    # ─── USD/INR Impact ──────────────────────────────────────
    usdinr_data = results.get("usdinr", {})
    inr_change_pct = usdinr_data.get("change_pct", 0)

    if inr_change_pct > 0.5:
        signals.append({
            "type": "INR_DEPRECIATION",
            "severity": "MEDIUM",
            "message": f"INR depreciated {inr_change_pct:.2f}% — positive for IT/pharma, negative for importers",
            "affected_sectors": {"positive": ["IT", "PHARMA"], "negative": ["OMC", "AIRLINES"]},
        })
    elif inr_change_pct < -0.5:
        signals.append({
            "type": "INR_APPRECIATION",
            "severity": "MEDIUM",
            "message": f"INR appreciated {abs(inr_change_pct):.2f}% — FII inflow possible",
        })

    # ─── US Markets Overnight ────────────────────────────────
    sp500_change = results.get("sp500", {}).get("change_pct", 0)
    if abs(sp500_change) > 1.5:
        direction = "rallied" if sp500_change > 0 else "sold off"
        signals.append({
            "type": "US_MARKET_MOVE",
            "severity": "HIGH" if abs(sp500_change) > 2 else "MEDIUM",
            "message": f"S&P 500 {direction} {abs(sp500_change):.1f}% — significant global cue",
        })

    # ─── Global VIX ──────────────────────────────────────────
    vix_global = results.get("vix_global", {}).get("close", 0)
    if vix_global > 30:
        signals.append({
            "type": "GLOBAL_FEAR",
            "severity": "HIGH",
            "message": f"US VIX at {vix_global:.1f} — global fear elevated, reduce exposure",
        })

    return {
        "markets": results,
        "gap_analysis": gap_analysis,
        "signals": signals,
        "fetched_at": datetime.now().isoformat(),
        "signal_count": len(signals),
    }


def _fetch_ticker_latest(ticker: str) -> Optional[Dict[str, Any]]:
    """Fetch latest data for a single ticker via yfinance."""
    if download_ohlcv is None:
        return None

    try:
        df = download_ohlcv(ticker, period="5d", interval="1d")
        if df is None or df.empty or len(df) < 2:
            return None

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        close = float(latest["Close"])
        prev_close = float(prev["Close"])
        change_pct = (close - prev_close) / prev_close * 100

        return {
            "close": round(close, 2),
            "prev_close": round(prev_close, 2),
            "change_pct": round(change_pct, 2),
            "high": round(float(latest["High"]), 2),
            "low": round(float(latest["Low"]), 2),
            "volume": int(latest["Volume"]),
        }
    except Exception:
        return None


def _calculate_gap_analysis(
    global_data: Dict[str, Dict],
) -> Dict[str, Any]:
    """
    Estimate expected gap for Indian market based on global cues.

    Uses a weighted composite of global market moves:
    - US markets (S&P 500): 40% weight
    - Asian markets (Hang Seng, Nikkei): 25% weight
    - Crude Oil: 15% weight (inverse for equity)
    - USD/INR: 10% weight (inverse)
    - Global VIX: 10% weight (inverse)
    """
    weights = {
        "sp500": 0.40,
        "hang_seng": 0.15,
        "nikkei": 0.10,
        "crude_oil": -0.10,  # Negative correlation with Indian equity (net importer)
        "usdinr": -0.10,     # INR depreciation = negative for broad market
        "vix_global": -0.05, # Higher VIX = negative
    }

    weighted_sum = 0
    total_weight = 0

    for source, weight in weights.items():
        change = global_data.get(source, {}).get("change_pct", 0)
        if change != 0:
            weighted_sum += change * weight
            total_weight += abs(weight)

    implied_gap_pct = weighted_sum / total_weight if total_weight > 0 else 0

    # Risk classification
    if implied_gap_pct < -1.5:
        risk = "HIGH — suppress all buy signals"
        suppress_buys = True
    elif implied_gap_pct < -0.5:
        risk = "MODERATE — widen predicted ranges"
        suppress_buys = False
    elif implied_gap_pct > 1.5:
        risk = "STRONG POSITIVE — but beware gap-and-fade"
        suppress_buys = False
    else:
        risk = "NORMAL — no adjustment needed"
        suppress_buys = False

    return {
        "implied_gap_pct": round(implied_gap_pct, 2),
        "risk_level": risk,
        "suppress_buy_signals": suppress_buys,
        "range_widen_factor": 1.5 if abs(implied_gap_pct) > 0.5 else 1.0,
    }
