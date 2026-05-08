"""
Agent Alpha v2.0 — FII/DII Daily Flow Fetcher
===============================================
Source: NSE India website
The most powerful freely-available signal in Indian equity markets.

FII (Foreign Institutional Investor) net buying/selling tells you where
the smart money is flowing. DII (Domestic Institutional Investor) flows
show domestic institutional conviction.

Signal Construction:
- Rolling 5-day and 20-day cumulative flows
- Consecutive buying/selling streak detection  
- ₹5000 Cr single-day sell → HARD VETO all buys for 2 days
"""
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import json
import time

# NSE requires specific headers to not get blocked
NSE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/market-data/live-market-statistics",
}

# Alpha Vantage / alternative free APIs for FII/DII
MONEYCONTROL_FII_URL = "https://api.moneycontrol.com/mcapi/v1/fii-dii/overview"


def _get_nse_session() -> requests.Session:
    """Create an NSE-ready session with proper cookies."""
    session = requests.Session()
    session.headers.update(NSE_HEADERS)
    # First hit the main page to get cookies
    try:
        session.get("https://www.nseindia.com", timeout=10)
        time.sleep(0.5)  # Rate limiting respect
    except Exception:
        pass
    return session


def fetch_fii_dii_daily() -> Optional[Dict[str, Any]]:
    """
    Fetch today's FII and DII net buy/sell data.
    
    Returns:
        Dict with keys: date, fii_net_cr, dii_net_cr, fii_buy_cr, fii_sell_cr,
                         dii_buy_cr, dii_sell_cr
        Or None if fetch fails.
    """
    # Attempt 1: NSE Direct API
    try:
        session = _get_nse_session()
        url = "https://www.nseindia.com/api/fiidiiTradeReact"
        resp = session.get(url, timeout=15)
        
        if resp.status_code == 200:
            data = resp.json()
            
            fii_data = None
            dii_data = None
            
            for entry in data:
                category = entry.get("category", "").upper()
                if "FII" in category or "FPI" in category:
                    fii_data = entry
                elif "DII" in category:
                    dii_data = entry
            
            if fii_data and dii_data:
                result = {
                    "date": fii_data.get("date", datetime.now().strftime("%d-%b-%Y")),
                    "fii_buy_cr": _parse_amount(fii_data.get("buyValue", 0)),
                    "fii_sell_cr": _parse_amount(fii_data.get("sellValue", 0)),
                    "fii_net_cr": _parse_amount(fii_data.get("netValue", 0)),
                    "dii_buy_cr": _parse_amount(dii_data.get("buyValue", 0)),
                    "dii_sell_cr": _parse_amount(dii_data.get("sellValue", 0)),
                    "dii_net_cr": _parse_amount(dii_data.get("netValue", 0)),
                    "source": "nse_direct",
                    "fetched_at": datetime.now().isoformat(),
                }
                print(f"✅ FII/DII data fetched from NSE: FII net={result['fii_net_cr']:.0f}Cr, DII net={result['dii_net_cr']:.0f}Cr")
                return result
    except Exception as e:
        print(f"⚠️ NSE FII/DII fetch failed: {e}")

    # Attempt 2: Fallback to MoneyControl API
    try:
        resp = requests.get(MONEYCONTROL_FII_URL, headers=NSE_HEADERS, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("data"):
                fii = data["data"].get("fii", {})
                dii = data["data"].get("dii", {})
                result = {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "fii_buy_cr": _parse_amount(fii.get("buyValue", 0)),
                    "fii_sell_cr": _parse_amount(fii.get("sellValue", 0)),
                    "fii_net_cr": _parse_amount(fii.get("netValue", 0)),
                    "dii_buy_cr": _parse_amount(dii.get("buyValue", 0)),
                    "dii_sell_cr": _parse_amount(dii.get("sellValue", 0)),
                    "dii_net_cr": _parse_amount(dii.get("netValue", 0)),
                    "source": "moneycontrol",
                    "fetched_at": datetime.now().isoformat(),
                }
                print(f"✅ FII/DII data fetched from MoneyControl fallback")
                return result
    except Exception as e:
        print(f"⚠️ MoneyControl FII/DII fallback failed: {e}")

    print("❌ All FII/DII data sources failed")
    return None


def _parse_amount(value) -> float:
    """Parse amount value that could be string or number, convert to Crores."""
    if value is None:
        return 0.0
    if isinstance(value, str):
        value = value.replace(",", "").replace("₹", "").strip()
        try:
            return float(value)
        except ValueError:
            return 0.0
    return float(value)


def calculate_fii_dii_signals(
    flow_history: List[Dict[str, Any]],
    consecutive_days_threshold: int = 3,
    cumulative_5d_threshold_cr: float = 2000,
    mass_selling_veto_cr: float = 5000,
) -> Dict[str, Any]:
    """
    Calculate FII/DII flow signals from historical flow data.
    
    Args:
        flow_history: List of daily flow dicts, sorted oldest to newest
        consecutive_days_threshold: Days of same direction for strong signal
        cumulative_5d_threshold_cr: Cumulative flow for strong signal (₹Cr)
        mass_selling_veto_cr: Single-day FII sell that triggers HARD VETO (₹Cr)
    
    Returns:
        Dict with: fii_flow_score, dii_flow_score, institutional_consensus,
                    fii_consecutive_days, dii_consecutive_days, hard_veto_active,
                    rolling_5d_fii, rolling_20d_fii, rolling_5d_dii, rolling_20d_dii
    """
    if not flow_history or len(flow_history) < 2:
        return {
            "fii_flow_score": 0, "dii_flow_score": 0,
            "institutional_consensus": "unknown",
            "hard_veto_active": False, "hard_veto_reason": None,
        }

    # Extract FII and DII net flows
    fii_nets = [f.get("fii_net_cr", 0) for f in flow_history]
    dii_nets = [f.get("dii_net_cr", 0) for f in flow_history]

    # ─── Rolling Cumulative Flows ────────────────────────────
    rolling_5d_fii = sum(fii_nets[-5:]) if len(fii_nets) >= 5 else sum(fii_nets)
    rolling_20d_fii = sum(fii_nets[-20:]) if len(fii_nets) >= 20 else sum(fii_nets)
    rolling_5d_dii = sum(dii_nets[-5:]) if len(dii_nets) >= 5 else sum(dii_nets)
    rolling_20d_dii = sum(dii_nets[-20:]) if len(dii_nets) >= 20 else sum(dii_nets)

    # ─── Consecutive Day Streaks ─────────────────────────────
    fii_consecutive = _count_consecutive_direction(fii_nets)
    dii_consecutive = _count_consecutive_direction(dii_nets)

    # ─── FII Flow Score ──────────────────────────────────────
    fii_score = 0
    if fii_consecutive >= 10 and fii_nets[-1] > 0:
        fii_score = 5   # Very strong accumulation (10+ days buying)
    elif fii_consecutive >= 5 and fii_nets[-1] > 0:
        fii_score = 3   # Strong accumulation
    elif fii_consecutive >= consecutive_days_threshold and fii_nets[-1] > 0:
        if rolling_5d_fii > cumulative_5d_threshold_cr:
            fii_score = 2
        else:
            fii_score = 1
    elif fii_consecutive >= 5 and fii_nets[-1] < 0:
        fii_score = -3  # Distribution
    elif fii_consecutive >= consecutive_days_threshold and fii_nets[-1] < 0:
        fii_score = -2

    # ─── DII Flow Score ──────────────────────────────────────
    dii_score = 0
    if dii_consecutive >= consecutive_days_threshold and dii_nets[-1] > 0:
        if rolling_5d_dii > cumulative_5d_threshold_cr:
            dii_score = 2
        else:
            dii_score = 1
    elif dii_consecutive >= consecutive_days_threshold and dii_nets[-1] < 0:
        dii_score = -2

    # ─── Institutional Consensus ─────────────────────────────
    fii_buying = fii_nets[-1] > 0
    dii_buying = dii_nets[-1] > 0
    
    if fii_buying and dii_buying:
        consensus = "strong_bullish"  # Both buying = high conviction
    elif not fii_buying and not dii_buying:
        consensus = "strong_bearish"  # Both selling = high conviction bearish
    elif not fii_buying and dii_buying:
        consensus = "divergent_dii_support"  # DII supporting while FII sells = reducing vol
    else:
        consensus = "divergent_fii_lead"  # FII buying, DII selling = follow FII

    # ─── Flow Acceleration ───────────────────────────────────
    # Is FII buying accelerating or decelerating?
    fii_acceleration = "steady"
    if len(fii_nets) >= 5:
        recent_avg = np.mean(fii_nets[-3:])
        older_avg = np.mean(fii_nets[-5:-2]) if len(fii_nets) >= 5 else 0
        if recent_avg > older_avg * 1.5 and recent_avg > 0:
            fii_acceleration = "accelerating"
            fii_score += 1
        elif recent_avg < older_avg * 0.5 and recent_avg > 0:
            fii_acceleration = "decelerating"

    # ─── HARD VETO: Mass FII Selling ─────────────────────────
    hard_veto = False
    hard_veto_reason = None
    
    # Check last day and day before
    for i in range(-1, max(-3, -len(fii_nets)) - 1, -1):
        if fii_nets[i] < -mass_selling_veto_cr:
            hard_veto = True
            hard_veto_reason = (
                f"FII net selling ₹{abs(fii_nets[i]):.0f}Cr on "
                f"{flow_history[i].get('date', 'recent day')} "
                f"(threshold: ₹{mass_selling_veto_cr:.0f}Cr)"
            )
            break

    return {
        "fii_flow_score": fii_score,
        "dii_flow_score": dii_score,
        "total_flow_score": fii_score + dii_score,
        "institutional_consensus": consensus,
        "fii_consecutive_days": fii_consecutive,
        "dii_consecutive_days": dii_consecutive,
        "fii_acceleration": fii_acceleration,
        "rolling_5d_fii_cr": round(rolling_5d_fii, 2),
        "rolling_20d_fii_cr": round(rolling_20d_fii, 2),
        "rolling_5d_dii_cr": round(rolling_5d_dii, 2),
        "rolling_20d_dii_cr": round(rolling_20d_dii, 2),
        "hard_veto_active": hard_veto,
        "hard_veto_reason": hard_veto_reason,
        "latest_fii_net_cr": round(fii_nets[-1], 2) if fii_nets else 0,
        "latest_dii_net_cr": round(dii_nets[-1], 2) if dii_nets else 0,
    }


def _count_consecutive_direction(values: List[float]) -> int:
    """Count consecutive days of same direction (positive or negative) from the end."""
    if not values:
        return 0
    
    direction = 1 if values[-1] > 0 else -1 if values[-1] < 0 else 0
    if direction == 0:
        return 0
    
    count = 0
    for val in reversed(values):
        if (direction > 0 and val > 0) or (direction < 0 and val < 0):
            count += 1
        else:
            break
    
    return count
