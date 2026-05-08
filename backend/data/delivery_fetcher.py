"""
Agent Alpha v2.0 — NSE Delivery Percentage Fetcher
====================================================
Source: NSE India publishes daily delivery percentage for every stock.

Delivery % measures what fraction of traded volume was actually delivered
(settled in demat) vs intraday speculation:

- High delivery % (>65%) = Strong conviction buying — buyers intend to HOLD
- Medium delivery % (40-65%) = Normal activity
- Low delivery % (<25%) = Speculative/intraday activity — less reliable signal

This is a uniquely Indian market metric that global quant funds don't have.
"""
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import time

NSE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/market-data/security-information",
}


def _get_nse_session() -> requests.Session:
    """Create an NSE-ready session with proper cookies."""
    session = requests.Session()
    session.headers.update(NSE_HEADERS)
    try:
        session.get("https://www.nseindia.com", timeout=10)
        time.sleep(0.5)
    except Exception:
        pass
    return session


def fetch_delivery_data(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Fetch delivery percentage for a stock from NSE.

    Args:
        symbol: NSE symbol (e.g., "RELIANCE", "TCS")

    Returns:
        Dict with: symbol, date, delivery_pct, traded_qty, delivered_qty,
                    delivery_score (-1, 0, or +2)
        Or None if fetch fails.
    """
    # Attempt: NSE Security Deliverable Data API
    try:
        session = _get_nse_session()
        url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}&section=trade_info"
        resp = session.get(url, timeout=15)

        if resp.status_code == 200:
            data = resp.json()
            
            sec_info = data.get("securityWiseDP", {})
            if sec_info:
                delivery_pct = _parse_float(sec_info.get("delToTradedQty", 0))
                traded_qty = _parse_float(sec_info.get("quantityTraded", 0))
                delivered_qty = _parse_float(sec_info.get("deliveryQuantity", 0))

                # Calculate conviction score
                score = _calculate_delivery_score(delivery_pct)

                result = {
                    "symbol": symbol,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "delivery_pct": round(delivery_pct, 2),
                    "traded_qty": traded_qty,
                    "delivered_qty": delivered_qty,
                    "delivery_score": score,
                    "conviction_label": _conviction_label(delivery_pct),
                    "source": "nse_direct",
                    "fetched_at": datetime.now().isoformat(),
                }
                print(f"✅ Delivery data for {symbol}: {delivery_pct:.1f}% → score={score}")
                return result
    except Exception as e:
        print(f"⚠️ NSE delivery fetch failed for {symbol}: {e}")

    # Fallback: Use volume-based approximation from OHLCV
    # (Less accurate but ensures we always have a value)
    return _approximate_delivery_from_volume(symbol)


def _approximate_delivery_from_volume(symbol: str) -> Optional[Dict[str, Any]]:
    """
    When NSE API is blocked, approximate delivery % from volume patterns.
    
    Heuristic: If today's volume is significantly higher than average 
    but price barely moved, it's likely intraday speculation (low delivery %).
    If volume is moderate and price moved directionally, higher delivery % likely.
    """
    try:
        from data.stock_fetcher import download_ohlcv
        
        df = download_ohlcv(f"{symbol}.NS", period="1mo", interval="1d")
        if df is None or len(df) < 5:
            return None
        
        latest = df.iloc[-1]
        avg_vol = df["Volume"].iloc[-20:].mean() if len(df) >= 20 else df["Volume"].mean()
        vol_ratio = latest["Volume"] / avg_vol if avg_vol > 0 else 1.0
        price_move = abs(latest["Close"] - latest["Open"]) / latest["Open"] * 100

        # Approximation logic:
        # High volume + small price move = intraday churn (low delivery)
        # Moderate volume + directional move = conviction (higher delivery)
        if vol_ratio > 2.0 and price_move < 0.5:
            approx_delivery = 25.0  # Likely speculative
        elif vol_ratio > 1.5 and price_move < 1.0:
            approx_delivery = 40.0
        elif price_move > 2.0:
            approx_delivery = 60.0  # Strong directional move
        else:
            approx_delivery = 50.0  # Default

        score = _calculate_delivery_score(approx_delivery)

        return {
            "symbol": symbol,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "delivery_pct": approx_delivery,
            "traded_qty": float(latest["Volume"]),
            "delivered_qty": float(latest["Volume"] * approx_delivery / 100),
            "delivery_score": score,
            "conviction_label": _conviction_label(approx_delivery),
            "source": "approximated",
            "fetched_at": datetime.now().isoformat(),
        }
    except Exception as e:
        print(f"⚠️ Delivery approximation failed for {symbol}: {e}")
        return None


def _calculate_delivery_score(delivery_pct: float) -> int:
    """
    Convert delivery percentage to a conviction score.

    Scoring (from alpha_config.yaml):
    - > 65% = +2 (High conviction buying)
    - 40-65% = 0 (Normal)
    - < 25% = -1 (Speculative)
    """
    if delivery_pct >= 65:
        return 2
    elif delivery_pct < 25:
        return -1
    return 0


def _conviction_label(delivery_pct: float) -> str:
    """Human-readable conviction label."""
    if delivery_pct >= 65:
        return "HIGH CONVICTION"
    elif delivery_pct >= 50:
        return "MODERATE CONVICTION"
    elif delivery_pct >= 25:
        return "LOW CONVICTION"
    else:
        return "SPECULATIVE"


def _parse_float(value) -> float:
    """Safely parse a value to float."""
    if value is None:
        return 0.0
    if isinstance(value, str):
        value = value.replace(",", "").replace("%", "").strip()
        try:
            return float(value)
        except ValueError:
            return 0.0
    return float(value)


def fetch_batch_delivery(symbols: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Fetch delivery data for multiple symbols.
    Rate-limited to respect NSE.
    
    Returns:
        Dict mapping symbol → delivery data dict
    """
    results = {}
    for i, sym in enumerate(symbols):
        data = fetch_delivery_data(sym)
        if data:
            results[sym] = data
        if i < len(symbols) - 1:
            time.sleep(0.3)  # Rate limit: 300ms between requests
    
    print(f"✅ Fetched delivery data for {len(results)}/{len(symbols)} symbols")
    return results
