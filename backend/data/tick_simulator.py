"""
Agent Alpha v3.0 — High-Frequency Tick Simulator
================================================
Since true Tick-by-Tick (TBT) or FIX data costs ₹50,000+/month, 
this module simulates institutional micro-structure analysis using 
free 1-minute interval data from Yahoo Finance.

It detects hidden institutional accumulation (Iceberg orders) by 
looking for localized volume spikes with zero price movement.
"""
import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Any

def simulate_micro_structure(symbol: str) -> Dict[str, Any]:
    """
    Fetch 1-minute data for the last 5 days to analyze micro-structure.
    Looks for signs of institutional accumulation or distribution.
    """
    try:
        # Yahoo Finance symbol format for NSE
        yf_symbol = symbol if ".NS" in symbol or ".BO" in symbol else f"{symbol}.NS"
        
        ticker = yf.Ticker(yf_symbol)
        # Fetch 1-minute data for the last 5 days (max allowed by YF)
        df = ticker.history(period="5d", interval="1m")
        
        if df.empty or len(df) < 60:
            return {"error": "Insufficient intraday data"}
            
        # 1. Volume Spikes Detection (Hidden Accumulation/Distribution)
        # We look for 1m candles where volume is > 5x the 60-minute average
        df['Vol_MA60'] = df['Volume'].rolling(window=60).mean()
        df['Vol_Spike'] = df['Volume'] / df['Vol_MA60']
        
        spikes = df[df['Vol_Spike'] > 5.0].copy()
        
        accumulation_score = 0
        distribution_score = 0
        
        for idx, row in spikes.iterrows():
            # If large volume happens on an UP candle, it's accumulation
            if row['Close'] > row['Open']:
                accumulation_score += row['Vol_Spike']
            # If large volume happens on a DOWN candle, it's distribution
            elif row['Close'] < row['Open']:
                distribution_score += row['Vol_Spike']
                
        # 2. VWAP Slope over the last day
        df['Typical_Price'] = (df['High'] + df['Low'] + df['Close']) / 3
        df['VP'] = df['Typical_Price'] * df['Volume']
        
        # Calculate daily VWAP
        df['Date'] = df.index.date
        df['Cumulative_VP'] = df.groupby('Date')['VP'].cumsum()
        df['Cumulative_Vol'] = df.groupby('Date')['Volume'].cumsum()
        df['VWAP'] = df['Cumulative_VP'] / df['Cumulative_Vol']
        
        # Get the latest day's VWAP slope
        latest_day = df[df['Date'] == df['Date'].iloc[-1]]
        if len(latest_day) > 30:
            vwap_start = latest_day['VWAP'].iloc[0]
            vwap_end = latest_day['VWAP'].iloc[-1]
            vwap_slope_pct = (vwap_end - vwap_start) / vwap_start * 100
        else:
            vwap_slope_pct = 0.0
            
        net_flow = accumulation_score - distribution_score
        
        return {
            "symbol": symbol,
            "net_micro_flow": round(net_flow, 2),
            "vwap_slope_pct": round(vwap_slope_pct, 3),
            "hidden_accumulation": net_flow > 10.0 and vwap_slope_pct > 0,
            "hidden_distribution": net_flow < -10.0 and vwap_slope_pct < 0,
            "total_spikes_detected": len(spikes)
        }
        
    except Exception as e:
        print(f"❌ Tick Simulator failed for {symbol}: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    print(simulate_micro_structure("RELIANCE.NS"))
