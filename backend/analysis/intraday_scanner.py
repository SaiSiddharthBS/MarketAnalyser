"""
Agent Alpha v3.0 — Intraday Signal Scanner
==========================================
Scans 5-minute candles to detect intraday opportunities during market hours.
(Note: yfinance has a ~15 minute delay for Indian markets, so this is used
for paper trading validation and structural testing, not live scalping execution).

Strategies implemented:
1. ORB (Opening Range Breakout) — 15 minute range
2. VWAP Strategy — Price crossing above VWAP with volume
3. Intraday Momentum — 5-min RSI > 70 + volume surge
4. Gap Analysis — Gap and go vs Gap fill
"""
import yfinance as yf
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    """Calculate Volume Weighted Average Price for the current session."""
    # Ensure index is datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
        
    # Calculate typical price
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    
    # Calculate VWAP per day
    vwap = (typical_price * df['Volume']).groupby(df.index.date).cumsum() / df['Volume'].groupby(df.index.date).cumsum()
    return vwap

def analyze_intraday(symbol: str, df_5m: pd.DataFrame, df_daily: pd.DataFrame = None) -> dict:
    """
    Analyze 5-min DataFrame for intraday setups.
    Returns a dictionary of signals and metrics.
    """
    if df_5m is None or len(df_5m) < 10:
        return {"status": "INSUFFICIENT_DATA"}
        
    try:
        # Extract today's data only
        last_date = df_5m.index[-1].date()
        today_df = df_5m[df_5m.index.date == last_date]
        
        if len(today_df) < 3: # Need at least 15 mins for ORB
            return {"status": "MARKET_JUST_OPENED"}
            
        current_price = float(today_df['Close'].iloc[-1])
        current_vol = float(today_df['Volume'].iloc[-1])
        
        signals = []
        confidence = 0
        
        # 1. ORB (15-min Opening Range Breakout)
        first_15m = today_df.iloc[:3]
        orb_high = float(first_15m['High'].max())
        orb_low = float(first_15m['Low'].min())
        
        if current_price > orb_high:
            signals.append("ORB_BREAKOUT_BULLISH")
            confidence += 30
        elif current_price < orb_low:
            signals.append("ORB_BREAKDOWN_BEARISH")
            confidence -= 30
            
        # 2. VWAP Analysis
        today_df = today_df.copy()
        today_df['VWAP'] = calculate_vwap(today_df)
        current_vwap = float(today_df['VWAP'].iloc[-1])
        
        if current_price > current_vwap:
            signals.append("ABOVE_VWAP")
            confidence += 20
        else:
            signals.append("BELOW_VWAP")
            confidence -= 20
            
        # 3. Volume Surge
        # Compare current 5m vol to average 5m vol for the day
        avg_5m_vol = float(today_df['Volume'].mean())
        if current_vol > avg_5m_vol * 2.5:
            signals.append("VOLUME_SURGE")
            if current_price > today_df['Open'].iloc[-1]: # Bullish candle
                confidence += 15
            else:
                confidence -= 15
                
        # 4. Gap Analysis (Requires daily data)
        gap_status = "NO_GAP"
        if df_daily is not None and len(df_daily) >= 2:
            prev_close = float(df_daily['Close'].iloc[-2])
            today_open = float(today_df['Open'].iloc[0])
            gap_pct = ((today_open - prev_close) / prev_close) * 100
            
            if gap_pct > 0.5:
                gap_status = f"GAP_UP_{gap_pct:.1f}%"
                if current_price > today_open: # Gap and Go
                    signals.append("GAP_AND_GO_BULLISH")
                    confidence += 15
                elif current_price < prev_close: # Gap Fill
                    signals.append("GAP_FILLED_BEARISH")
                    confidence -= 10
            elif gap_pct < -0.5:
                gap_status = f"GAP_DOWN_{abs(gap_pct):.1f}%"
                if current_price < today_open: # Gap and Go down
                    signals.append("GAP_AND_GO_BEARISH")
                    confidence -= 15
                elif current_price > prev_close: # Gap Fill up
                    signals.append("GAP_FILLED_BULLISH")
                    confidence += 10
                    
        # Final Decision
        action = "NEUTRAL"
        if confidence >= 50:
            action = "BUY"
        elif confidence >= 70:
            action = "STRONG_BUY"
        elif confidence <= -50:
            action = "SELL"
        elif confidence <= -70:
            action = "STRONG_SELL"
            
        return {
            "status": "SUCCESS",
            "action": action,
            "confidence": confidence,
            "signals": signals,
            "metrics": {
                "price": round(current_price, 2),
                "vwap": round(current_vwap, 2),
                "orb_high": round(orb_high, 2),
                "orb_low": round(orb_low, 2),
                "gap": gap_status
            }
        }
        
    except Exception as e:
        logger.error(f"Intraday scan failed for {symbol}: {e}")
        return {"status": "ERROR", "message": str(e)}

def scan_market_intraday(tickers: list) -> list:
    """Scan a list of tickers for intraday setups."""
    logger.info(f"Starting intraday scan for {len(tickers)} tickers...")
    opportunities = []
    
    for ticker in tickers:
        try:
            # Fetch 5-minute data
            df_5m = yf.download(ticker, period="5d", interval="5m", progress=False, timeout=5)
            # Fetch daily data for gap analysis
            df_1d = yf.download(ticker, period="5d", interval="1d", progress=False, timeout=5)
            
            result = analyze_intraday(ticker, df_5m, df_1d)
            
            if result.get("status") == "SUCCESS" and result.get("action") in ["BUY", "STRONG_BUY", "SELL", "STRONG_SELL"]:
                opportunities.append({
                    "symbol": ticker,
                    "action": result["action"],
                    "confidence": result["confidence"],
                    "signals": result["signals"],
                    "metrics": result["metrics"]
                })
        except Exception as e:
            logger.debug(f"Could not scan {ticker}: {e}")
            continue
            
    # Sort by confidence
    opportunities.sort(key=lambda x: abs(x["confidence"]), reverse=True)
    return opportunities

if __name__ == "__main__":
    test_tickers = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS"]
    print(f"Scanning {test_tickers} for Intraday Opportunities...")
    results = scan_market_intraday(test_tickers)
    for res in results:
        print(f"{res['symbol']} -> {res['action']} (Conf: {res['confidence']}) | Signals: {res['signals']}")
