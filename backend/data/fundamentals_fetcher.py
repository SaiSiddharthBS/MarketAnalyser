import yfinance as yf
import json
import logging
from datetime import datetime
import pandas as pd
import database as db

logger = logging.getLogger(__name__)

def fetch_fundamentals(symbol: str) -> dict:
    """Fetch fundamental metrics for factor models (Value, Quality)."""
    # Check cache first (Fundamentals only change quarterly, so caching for 7 days is safe)
    # We will use the existing cache table or just cache daily.
    ticker = f"{symbol}.NS"
    try:
        t = yf.Ticker(ticker)
        info = t.info
        
        # Extract Value Factors
        pe = info.get("trailingPE", None)
        pb = info.get("priceToBook", None)
        ev_ebitda = info.get("enterpriseToEbitda", None)
        
        # Extract Quality Factors
        roe = info.get("returnOnEquity", None)
        debt_to_equity = info.get("debtToEquity", None)
        profit_margins = info.get("profitMargins", None)
        
        # Extract Earnings Surprise
        eps_trailing = info.get("trailingEps", None)
        eps_forward = info.get("forwardEps", None)
        
        # We need a robust fallback if None
        data = {
            "pe": pe if pe is not None else 0.0,
            "pb": pb if pb is not None else 0.0,
            "ev_ebitda": ev_ebitda if ev_ebitda is not None else 0.0,
            "roe": roe if roe is not None else 0.0,
            "debt_to_equity": debt_to_equity if debt_to_equity is not None else 0.0,
            "profit_margins": profit_margins if profit_margins is not None else 0.0,
            "eps_growth_est": ((eps_forward - eps_trailing) / eps_trailing) if eps_forward and eps_trailing and eps_trailing > 0 else 0.0
        }
        return data
        
    except Exception as e:
        logger.error(f"Failed to fetch fundamentals for {symbol}: {e}")
        return {}

def bulk_fetch_fundamentals(symbols: list) -> dict:
    results = {}
    for sym in symbols:
        results[sym] = fetch_fundamentals(sym)
    return results

if __name__ == "__main__":
    print(fetch_fundamentals("RELIANCE"))
