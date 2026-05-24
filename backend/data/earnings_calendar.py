"""
Agent Alpha v6+ — Earnings Calendar Fetcher
============================================
Checks if a stock has upcoming earnings/results within N trading days.
Uses yfinance's earnings calendar as primary source.
Integrated into the veto pipeline to flag or block trades near earnings.
"""
import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# In-memory cache to avoid repeated API calls within the same screener run
_earnings_cache: Dict[str, Dict[str, Any]] = {}
_cache_date: Optional[str] = None


def get_days_to_earnings(symbol: str) -> Dict[str, Any]:
    """
    Check how many calendar days until the next earnings announcement.
    
    Returns:
        Dict with:
            - days_to_earnings: int or None if unknown
            - earnings_date: str or None
            - available: bool
    """
    global _earnings_cache, _cache_date
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # Reset cache at the start of each new day
    if _cache_date != today_str:
        _earnings_cache = {}
        _cache_date = today_str
    
    # Return cached result if available
    if symbol in _earnings_cache:
        return _earnings_cache[symbol]
    
    result = {"days_to_earnings": None, "earnings_date": None, "available": False}
    
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        cal = ticker.calendar
        
        if cal is not None and not (hasattr(cal, 'empty') and cal.empty):
            # yfinance calendar can return a DataFrame or dict depending on version
            earnings_date = None
            
            if isinstance(cal, dict):
                # Newer yfinance versions return dict
                ed = cal.get("Earnings Date")
                if ed:
                    if isinstance(ed, list) and len(ed) > 0:
                        earnings_date = ed[0]
                    else:
                        earnings_date = ed
            else:
                # Older versions return DataFrame
                try:
                    if "Earnings Date" in cal.columns:
                        ed_val = cal["Earnings Date"].iloc[0]
                        earnings_date = ed_val
                    elif "Earnings Date" in cal.index:
                        ed_val = cal.loc["Earnings Date"]
                        if hasattr(ed_val, 'iloc'):
                            earnings_date = ed_val.iloc[0]
                        else:
                            earnings_date = ed_val
                except Exception:
                    pass
            
            if earnings_date is not None:
                # Convert to datetime if needed
                import pandas as pd
                if isinstance(earnings_date, str):
                    earnings_dt = pd.to_datetime(earnings_date)
                elif hasattr(earnings_date, 'date'):
                    earnings_dt = earnings_date
                else:
                    earnings_dt = pd.to_datetime(str(earnings_date))
                
                today = pd.Timestamp.now().normalize()
                if hasattr(earnings_dt, 'tz') and earnings_dt.tz is not None:
                    earnings_dt = earnings_dt.tz_localize(None)
                
                days_diff = (earnings_dt - today).days
                
                # Only care about upcoming earnings (not past)
                if days_diff >= -2:  # Include 2 days after results too
                    result = {
                        "days_to_earnings": max(0, days_diff),
                        "earnings_date": earnings_dt.strftime("%Y-%m-%d"),
                        "available": True,
                    }
    except Exception as e:
        # Silently fail — earnings data is supplementary, not critical
        pass
    
    _earnings_cache[symbol] = result
    return result


def get_earnings_flag(symbol: str) -> Optional[str]:
    """
    Get a human-readable earnings warning flag for a stock.
    Returns None if no earnings concern.
    
    Integration point: Called from technical.py pipeline.
    """
    data = get_days_to_earnings(symbol)
    
    if not data["available"]:
        return None
    
    days = data["days_to_earnings"]
    date_str = data["earnings_date"]
    
    if days is not None:
        if days <= 3:
            return f"🚫 EARNINGS BLACKOUT — Results expected {date_str} ({days} days). High event risk."
        elif days <= 7:
            return f"⚠️ Results in {days} days ({date_str}) — elevated event risk"
        elif days <= 14:
            return f"📅 Results in {days} days ({date_str}) — monitor closely"
    
    return None
