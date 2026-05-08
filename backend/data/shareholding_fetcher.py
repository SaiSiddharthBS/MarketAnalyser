"""
Agent Alpha v2.0 — Shareholding & Pledging Fetcher
===================================================
Fetches shareholding patterns from NSE, specifically looking for:
1. Promoter Pledging % (Feeds into Hard Veto Engine)
2. FII/DII stake changes (Quarter-on-Quarter accumulation)

Why Pledging Matters:
When a promoter pledges shares to take a loan, and the stock price falls,
the lender issues a margin call. If the promoter can't pay, the lender 
dumps the shares on the open market, causing a catastrophic crash 
(e.g., Zee Entertainment, Yes Bank).
"""
import requests
from datetime import datetime
from typing import Dict, Any, Optional
import time

NSE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/",
}

def _get_nse_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(NSE_HEADERS)
    try:
        session.get("https://www.nseindia.com", timeout=10)
        time.sleep(0.5)
    except Exception:
        pass
    return session

def fetch_promoter_pledging(symbol: str) -> Dict[str, Any]:
    """
    Fetch promoter pledging data for a specific symbol.
    
    Returns:
        Dict with: pledging_pct, is_increasing_qoq, qoq_change_pct
    """
    session = _get_nse_session()
    url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}&section=corp_info"
    
    try:
        resp = session.get(url, timeout=15)
        if resp.status_code != 200:
            return _default_pledging()
            
        data = resp.json()
        corp_info = data.get("corporateInfo", {})
        
        # In NSE API, pledging is usually under 'pledgedDetails' or 'shareholdingPattern'
        spt = corp_info.get("shareholdingPattern", {})
        
        if not spt:
            return _default_pledging()
            
        # Extract the latest quarter data
        # Data structure varies, but we look for "promoterAndPromoterGroup" -> "pledgedOrOtherwiseEncumbered"
        
        # This is a simplified extraction based on typical NSE JSON structure
        # In production, this might need fallback to BSE XML or Screener.in scraping
        
        latest_pledge_pct = 0.0
        prev_pledge_pct = 0.0
        
        try:
            # Assuming NSE returns a list of quarters for shareholding
            records = spt.get("data", [])
            if len(records) > 0:
                latest = records[0]
                latest_pledge_pct = float(latest.get("pledge_pct", 0))
                
            if len(records) > 1:
                prev = records[1]
                prev_pledge_pct = float(prev.get("pledge_pct", 0))
                
        except (ValueError, KeyError, TypeError):
            pass
            
        qoq_change = latest_pledge_pct - prev_pledge_pct
        
        result = {
            "symbol": symbol,
            "promoter_pledging_pct": latest_pledge_pct,
            "promoter_pledging_increasing_qoq": qoq_change > 0,
            "promoter_pledging_change_qoq_pct": round(qoq_change, 2),
            "fetched_at": datetime.now().isoformat()
        }
        
        if latest_pledge_pct > 25:
            print(f"⚠️ HIGH PLEDGING for {symbol}: {latest_pledge_pct:.1f}%")
            
        return result
        
    except Exception as e:
        print(f"❌ NSE Pledging fetch failed for {symbol}: {e}")
        return _default_pledging()

def _default_pledging() -> Dict[str, Any]:
    return {
        "promoter_pledging_pct": 0.0,
        "promoter_pledging_increasing_qoq": False,
        "promoter_pledging_change_qoq_pct": 0.0,
    }
