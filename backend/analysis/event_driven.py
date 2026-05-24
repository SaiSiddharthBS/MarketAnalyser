"""
Agent Alpha — Corporate Event Engine
=====================================
Monitors corporate actions such as upcoming earnings, dividends, splits,
and buybacks. This allows the system to adjust risk (e.g. tightening stops before earnings)
or find event-driven momentum opportunities.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

def check_upcoming_earnings(symbol: str, exchange: str = "NS", days_ahead: int = 14) -> Dict[str, Any]:
    """
    Check if a company is reporting earnings within the next X days.
    """
    ticker_sym = f"{symbol}.{exchange}" if exchange else symbol
    try:
        ticker = yf.Ticker(ticker_sym)
        cal = ticker.calendar
        if not cal:
            return {"reporting_soon": False}
        
        # yfinance sometimes returns a dict with 'Earnings Date' as a list of dates
        earnings_dates = cal.get("Earnings Date", [])
        if not earnings_dates:
            return {"reporting_soon": False}
            
        today = datetime.now().date()
        cutoff = today + timedelta(days=days_ahead)
        
        for e_date in earnings_dates:
            if isinstance(e_date, datetime):
                e_date = e_date.date()
            if today <= e_date <= cutoff:
                days_until = (e_date - today).days
                return {
                    "reporting_soon": True,
                    "earnings_date": e_date.isoformat(),
                    "days_until": days_until,
                    "action": "TIGHTEN_STOPS" if days_until <= 3 else "MONITOR"
                }
                
        return {"reporting_soon": False}
    except Exception as e:
        logger.debug(f"Earnings fetch failed for {symbol}: {e}")
        return {"reporting_soon": False}

def check_corporate_actions(symbol: str, exchange: str = "NS", days_ahead: int = 14) -> Dict[str, Any]:
    """
    Check for upcoming Ex-Dividend dates or Stock Splits.
    """
    ticker_sym = f"{symbol}.{exchange}" if exchange else symbol
    try:
        ticker = yf.Ticker(ticker_sym)
        actions = ticker.actions
        if actions is None or actions.empty:
            return {"has_action": False}
            
        # Filter for future actions (yfinance usually returns past, but sometimes future ex-dates are visible if announced)
        # We can also check recent actions (past 5 days) to explain sudden price drops (e.g. stock split)
        today = pd.Timestamp(datetime.now().date(), tz="Asia/Kolkata")
        cutoff = today + pd.Timedelta(days=days_ahead)
        recent = today - pd.Timedelta(days=5)
        
        # Ensure index is timezone aware for comparison
        if actions.index.tzinfo is None:
            actions.index = actions.index.tz_localize("UTC").tz_convert("Asia/Kolkata")
            
        upcoming = actions[(actions.index >= recent) & (actions.index <= cutoff)]
        
        if upcoming.empty:
            return {"has_action": False}
            
        latest = upcoming.iloc[-1]
        action_date = upcoming.index[-1].date()
        
        is_split = float(latest.get("Stock Splits", 0)) > 0
        is_div = float(latest.get("Dividends", 0)) > 0
        
        return {
            "has_action": True,
            "action_date": action_date.isoformat(),
            "is_split": is_split,
            "is_dividend": is_div,
            "split_ratio": float(latest.get("Stock Splits", 0)),
            "dividend_amount": float(latest.get("Dividends", 0))
        }
    except Exception as e:
        logger.debug(f"Corporate actions fetch failed for {symbol}: {e}")
        return {"has_action": False}

def check_buyback_proxy(symbol: str, exchange: str = "NS") -> Dict[str, Any]:
    """
    Proxy for detecting buybacks by tracking 'sharesOutstanding' changes if available.
    Because live buyback data is hard to get, we use sharesOutstanding from info.
    """
    ticker_sym = f"{symbol}.{exchange}" if exchange else symbol
    try:
        ticker = yf.Ticker(ticker_sym)
        info = ticker.info
        shares = info.get("sharesOutstanding")
        implied_buyback = info.get("impliedSharesOutstanding", 0) < (shares or 0) # Just a rough heuristic if available
        
        if shares and implied_buyback:
            return {"active_buyback_proxy": True, "shares": shares}
            
        return {"active_buyback_proxy": False}
    except Exception as e:
        return {"active_buyback_proxy": False}

def scan_all_events(symbol: str, exchange: str = "NS") -> Dict[str, Any]:
    """
    Aggregates all corporate events for a single stock.
    """
    earnings = check_upcoming_earnings(symbol, exchange)
    actions = check_corporate_actions(symbol, exchange)
    buyback = check_buyback_proxy(symbol, exchange)
    
    has_any_event = earnings.get("reporting_soon") or actions.get("has_action") or buyback.get("active_buyback_proxy")
    
    return {
        "symbol": symbol,
        "has_events": has_any_event,
        "earnings": earnings,
        "actions": actions,
        "buyback": buyback
    }

if __name__ == "__main__":
    print(scan_all_events("RELIANCE"))
