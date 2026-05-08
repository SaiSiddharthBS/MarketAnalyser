"""
Agent Alpha v2.0 — Insider/SAST Disclosures Fetcher
===================================================
Fetches SEBI-mandated insider trading and SAST (Substantial Acquisition 
of Shares and Takeovers) disclosures directly from NSE.

Why it matters:
- Promoters buying their own stock in the open market is the highest 
  conviction signal in finance. They know the reality behind the numbers.
- We filter specifically for "Market Purchase" by "Promoters".
"""
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import time

NSE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/companies-listing/corporate-filings-insider-trading",
}

def _get_nse_session() -> requests.Session:
    """Create an NSE-ready session."""
    session = requests.Session()
    session.headers.update(NSE_HEADERS)
    try:
        session.get("https://www.nseindia.com", timeout=10)
        time.sleep(0.5)
    except Exception:
        pass
    return session

def fetch_insider_disclosures(days_back: int = 7) -> List[Dict[str, Any]]:
    """
    Fetch insider trading disclosures from NSE.
    
    Args:
        days_back: Number of days to look back
        
    Returns:
        List of parsed disclosure records
    """
    session = _get_nse_session()
    
    # NSE uses a 3-month rolling window for its default API
    # URL: https://www.nseindia.com/api/corporates-pit?index=equities
    url = "https://www.nseindia.com/api/corporates-pit?index=equities"
    
    try:
        resp = session.get(url, timeout=15)
        if resp.status_code != 200:
            print(f"⚠️ NSE Insider API returned {resp.status_code}")
            return []
            
        data = resp.json()
        records = data.get("data", [])
        
        parsed_records = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        for r in records:
            # Parse date
            date_str = r.get("date", "")
            try:
                # Typical format: 05-May-2024
                date_obj = datetime.strptime(date_str, "%d-%b-%Y")
                if date_obj < cutoff_date:
                    continue
            except ValueError:
                continue
                
            symbol = r.get("symbol", "")
            person_category = str(r.get("personCategory", "")).upper()
            acq_mode = str(r.get("modeOfAcquisition", "")).upper()
            
            # We are primarily interested in Promoters and KMP making Open Market Purchases
            if "PROMOTER" in person_category or "KMP" in person_category or "DIRECTOR" in person_category:
                
                # Filter for open market transactions
                if "MARKET PURCHASE" in acq_mode or "MARKET SALE" in acq_mode:
                    
                    transaction_type = "BUY" if "PURCHASE" in acq_mode else "SELL"
                    
                    # NSE provides values usually as strings with commas
                    try:
                        value_str = str(r.get("secVal", "0")).replace(",", "")
                        value = float(value_str)
                    except ValueError:
                        value = 0.0
                        
                    try:
                        qty_str = str(r.get("secAcq", "0")).replace(",", "")
                        qty = float(qty_str)
                    except ValueError:
                        qty = 0.0
                        
                    parsed_records.append({
                        "symbol": symbol,
                        "disclosure_date": date_obj.strftime("%Y-%m-%d"),
                        "company": r.get("company", ""),
                        "acquirer_name": r.get("acqName", ""),
                        "category": "PROMOTER" if "PROMOTER" in person_category else "KMP",
                        "transaction_type": transaction_type,
                        "quantity": qty,
                        "value": value,
                        "mode": acq_mode
                    })
                    
        print(f"✅ Fetched {len(parsed_records)} relevant insider trades from last {days_back} days.")
        return parsed_records
        
    except Exception as e:
        print(f"❌ NSE Insider fetch failed: {e}")
        return []

def fetch_sast_disclosures(days_back: int = 7) -> List[Dict[str, Any]]:
    """
    Fetch SAST (Substantial Acquisition) disclosures.
    These indicate large threshold crossings (e.g., >5% stake).
    """
    session = _get_nse_session()
    url = "https://www.nseindia.com/api/corporates-sast?index=equities"
    
    try:
        resp = session.get(url, timeout=15)
        if resp.status_code != 200:
            return []
            
        data = resp.json()
        records = data.get("data", [])
        
        parsed_records = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        for r in records:
            date_str = r.get("date", "")
            try:
                date_obj = datetime.strptime(date_str, "%d-%b-%Y")
                if date_obj < cutoff_date:
                    continue
            except ValueError:
                continue
                
            # Parse percentage changes
            try:
                pre_holding = float(str(r.get("totalHoldPreAcqPct", "0")).replace(",", ""))
                post_holding = float(str(r.get("totalHoldPostAcqPct", "0")).replace(",", ""))
            except ValueError:
                continue
                
            # Calculate crossing direction
            direction = "crossing_up" if post_holding > pre_holding else "crossing_down"
            
            # Detect major threshold crossings (5%, 10%, 25%)
            threshold = 0
            for t in [5, 10, 25, 50, 75]:
                if pre_holding < t and post_holding >= t:
                    threshold = t
                    break
                    
            parsed_records.append({
                "symbol": r.get("symbol", ""),
                "disclosure_date": date_obj.strftime("%Y-%m-%d"),
                "company": r.get("company", ""),
                "acquirer_name": r.get("acqName", ""),
                "category": "SAST",
                "transaction_type": "BUY" if direction == "crossing_up" else "SELL",
                "pre_holding_pct": pre_holding,
                "post_holding_pct": post_holding,
                "direction": direction,
                "threshold_pct": threshold
            })
            
        return parsed_records
        
    except Exception as e:
        print(f"❌ NSE SAST fetch failed: {e}")
        return []
