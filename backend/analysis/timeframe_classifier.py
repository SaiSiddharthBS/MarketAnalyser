"""
Agent Alpha v3.0 — Timeframe Classifier
=======================================
Institutional holding period classification engine.
Analyzes volatility, momentum, support/resistance distance, and volume
to predict the optimal holding period for a given BUY setup.

Categories:
- INTRADAY: Exit by 3:15 PM today
- SHORT_TERM: Hold 2-5 days
- SWING: Hold 5-20 days (Default)
- POSITIONAL: Hold 1-3 months
- LONG_TERM: Hold 3-12 months
"""
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Average True Range."""
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    return true_range.rolling(period).mean()

def classify_timeframe(df: pd.DataFrame, symbol: str) -> dict:
    """
    Classify the ideal holding timeframe for a stock.
    Returns dict with holding_class, expected_days, and confidence.
    """
    if df is None or len(df) < 60:
        return {
            "holding_class": "SWING",
            "expected_days": 10,
            "confidence": 50.0,
            "reason": "Insufficient data, defaulting to SWING"
        }
        
    try:
        current_close = float(df["Close"].iloc[-1])
        current_vol = float(df["Volume"].iloc[-1])
        avg_vol_20 = float(df["Volume"].rolling(20).mean().iloc[-1])
        
        # 1. Volatility Assessment (ATR %)
        atr_14 = calculate_atr(df, 14).iloc[-1]
        atr_pct = (atr_14 / current_close) * 100
        
        # 2. Resistance Distance (52-week high)
        high_52w = float(df["High"].rolling(250, min_periods=60).max().iloc[-1])
        dist_to_resistance = ((high_52w - current_close) / current_close) * 100
        
        # 3. Trend Consistency (20 EMA vs 50 EMA vs 200 EMA)
        ema_20 = df["Close"].ewm(span=20, adjust=False).mean().iloc[-1]
        ema_50 = df["Close"].ewm(span=50, adjust=False).mean().iloc[-1]
        ema_200 = df["Close"].ewm(span=200, adjust=False).mean().iloc[-1]
        
        strong_uptrend = (current_close > ema_20) and (ema_20 > ema_50) and (ema_50 > ema_200)
        
        # 4. Volume Profile
        rvol = current_vol / avg_vol_20 if avg_vol_20 > 0 else 1.0
        
        # --- SCORING LOGIC ---
        scores = {
            "INTRADAY": 0,
            "SHORT_TERM": 0,
            "SWING": 0,
            "POSITIONAL": 0,
            "LONG_TERM": 0
        }
        
        # Volatility rules
        if atr_pct > 5.0: # Extremely volatile
            scores["INTRADAY"] += 30
            scores["SHORT_TERM"] += 20
            scores["LONG_TERM"] -= 20
        elif atr_pct < 2.0: # Stable
            scores["POSITIONAL"] += 20
            scores["LONG_TERM"] += 30
            scores["INTRADAY"] -= 10
            
        # Resistance rules
        if dist_to_resistance < 2.0: # Right at major resistance
            scores["INTRADAY"] += 20
            scores["SHORT_TERM"] += 20
            scores["POSITIONAL"] -= 10 # Wait for breakout confirmation
        elif dist_to_resistance > 15.0: # Lots of room to run
            scores["SWING"] += 20
            scores["POSITIONAL"] += 20
            
        # Trend rules
        if strong_uptrend:
            scores["POSITIONAL"] += 25
            scores["LONG_TERM"] += 30
        else:
            # Reversal or chop
            scores["SHORT_TERM"] += 15
            scores["SWING"] += 15
            scores["LONG_TERM"] -= 30
            
        # Volume rules
        if rvol > 3.0: # Massive institutional volume
            scores["POSITIONAL"] += 15 # Institutional buying supports longer holds
            scores["SWING"] += 10
        elif rvol > 1.5:
            scores["SHORT_TERM"] += 10
            scores["SWING"] += 15
            
        # Find the winner
        best_class = max(scores, key=scores.get)
        confidence = min(100.0, max(20.0, scores[best_class] * 1.5))
        
        expected_days = {
            "INTRADAY": 0,
            "SHORT_TERM": 3,
            "SWING": 12,
            "POSITIONAL": 45,
            "LONG_TERM": 150
        }[best_class]
        
        reason = f"ATR: {atr_pct:.1f}%, Dist to Res: {dist_to_resistance:.1f}%, Trend: {'Strong' if strong_uptrend else 'Weak'}, RVOL: {rvol:.1f}"
        
        return {
            "holding_class": best_class,
            "expected_days": expected_days,
            "confidence": round(confidence, 1),
            "reason": reason,
            "scores": scores
        }
        
    except Exception as e:
        logger.error(f"Timeframe classification failed for {symbol}: {e}")
        return {
            "holding_class": "SWING",
            "expected_days": 10,
            "confidence": 50.0,
            "reason": "Error during classification"
        }

if __name__ == "__main__":
    import yfinance as yf
    symbol = "RELIANCE.NS"
    df = yf.download(symbol, period="1y", progress=False)
    res = classify_timeframe(df, symbol)
    print(f"Timeframe for {symbol}: {res['holding_class']} (Confidence: {res['confidence']}%)")
    print(f"Reason: {res['reason']}")
    print(f"Scores: {res['scores']}")
