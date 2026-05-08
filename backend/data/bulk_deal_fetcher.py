"""
Agent Alpha v2.0 — Bulk & Block Deals Fetcher
==============================================
Monitors institutional activity via SEBI-mandated Bulk Deal reporting.
A Bulk Deal is any transaction where total quantity bought/sold is 
more than 0.5% of the number of equity shares of the company.

Signal Value:
- High quality institution (e.g., Vanguard, SBI MF, sovereign funds) 
  buying large stakes is highly bullish.
- Promoters or PE funds selling large stakes in block deals creates supply overhang.
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
    "Referer": "https://www.nseindia.com/market-data/bulk-deal",
}

# A list of recognizable institutional names to flag high-quality buying/selling
SMART_MONEY_KEYWORDS = [
    "MUTUAL FUND", "MF", "VANGUARD", "BLACKROCK", "NORGES", "GOVERNMENT OF SINGAPORE",
    "MONET", "CAPITAL", "INVESTMENT", "MORGAN STANLEY", "GOLDMAN", "SOCIETE GENERALE",
    "NOMURA", "FIDELITY", "JPMORGAN", "CITIGROUP", "ABU DHABI", "ICICI PRUDENTIAL",
    "HDFC MUTUAL", "SBI MUTUAL", "NIPPON", "KOTAK", "UTI"
]

def _get_nse_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(NSE_HEADERS)
    try:
        session.get("https://www.nseindia.com", timeout=10)
        time.sleep(0.5)
    except Exception:
        pass
    return session

def fetch_bulk_deals(days_back: int = 1) -> List[Dict[str, Any]]:
    """
    Fetch Bulk Deals from NSE.
    Returns:
        List of parsed bulk deal records.
    """
    session = _get_nse_session()
    url = "https://www.nseindia.com/api/historical/bulk-deals"
    
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
                
            client_name = str(r.get("clientName", "")).upper()
            transaction_type = str(r.get("buySell", "")).upper()
            
            # Check if this is "smart money"
            is_smart_money = any(keyword in client_name for keyword in SMART_MONEY_KEYWORDS)
            
            try:
                qty = float(str(r.get("quantity", "0")).replace(",", ""))
                price = float(str(r.get("tradePrice", "0")).replace(",", ""))
                value = qty * price
            except ValueError:
                continue
                
            parsed_records.append({
                "symbol": r.get("symbol", ""),
                "date": date_obj.strftime("%Y-%m-%d"),
                "client_name": client_name,
                "transaction_type": "BUY" if transaction_type == "BUY" else "SELL",
                "quantity": qty,
                "price": price,
                "value": value,
                "is_smart_money": is_smart_money,
                "remarks": r.get("remarks", "")
            })
            
        # Optional: Consolidate deals for the same stock if multiple occurred today
        # Because sometimes an institution buys 5% and another institution sells 5% (handshake deal)
        
        return parsed_records
        
    except Exception as e:
        print(f"❌ NSE Bulk Deal fetch failed: {e}")
        return []

def analyze_bulk_deals_for_symbol(symbol: str, deals: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze bulk deals for a specific stock to generate an institutional footprint score.
    """
    symbol_deals = [d for d in deals if d.get("symbol", "").upper() == symbol.upper()]
    
    if not symbol_deals:
        return {"signal": "NEUTRAL", "net_institutional_flow": 0}
        
    net_smart_money_flow = 0
    smart_buyers = []
    smart_sellers = []
    
    for d in symbol_deals:
        if d.get("is_smart_money"):
            val = d.get("value", 0)
            if d.get("transaction_type") == "BUY":
                net_smart_money_flow += val
                smart_buyers.append(d.get("client_name"))
            else:
                net_smart_money_flow -= val
                smart_sellers.append(d.get("client_name"))
                
    if net_smart_money_flow > 50_00_00_000: # > 50 Cr net smart money buying
        signal = "BUY"
    elif net_smart_money_flow < -50_00_00_000: # > 50 Cr net smart money selling
        signal = "SELL"
    else:
        signal = "NEUTRAL"
        
    return {
        "signal": signal,
        "net_institutional_flow_cr": round(net_smart_money_flow / 10000000, 2),
        "smart_buyers": list(set(smart_buyers)),
        "smart_sellers": list(set(smart_sellers)),
        "deal_count": len(symbol_deals)
    }
