import pandas as pd
import numpy as np

def detect_patterns(df: pd.DataFrame) -> dict:
    """
    Detects 5 basic chart patterns: 
    Double Bottom, Double Top, Bullish Engulfing, Bearish Engulfing, Morning Star.
    Returns the most confident pattern detected (if any), else None.
    """
    if len(df) < 20:
        return {"pattern_name": "None", "confidence": 0, "direction": "neutral"}
        
    patterns_found = []
    
    # 1. Bullish & Bearish Engulfing
    # Needs last 2 candles
    curr = df.iloc[-1]
    prev = df.iloc[-2]
    
    curr_body = abs(curr['Close'] - curr['Open'])
    prev_body = abs(prev['Close'] - prev['Open'])
    
    # Bullish Engulfing: prev is red, curr is green, curr body covers prev body
    if prev['Close'] < prev['Open'] and curr['Close'] > curr['Open']:
        if curr['Close'] >= prev['Open'] and curr['Open'] <= prev['Close'] and curr_body > prev_body:
            patterns_found.append({"pattern_name": "Bullish Engulfing", "confidence": 80, "direction": "bullish"})
            
    # Bearish Engulfing: prev is green, curr is red, curr body covers prev body
    if prev['Close'] > prev['Open'] and curr['Close'] < curr['Open']:
        if curr['Open'] >= prev['Close'] and curr['Close'] <= prev['Open'] and curr_body > prev_body:
            patterns_found.append({"pattern_name": "Bearish Engulfing", "confidence": 80, "direction": "bearish"})
            
    # 2. Morning Star
    # Needs last 3 candles
    if len(df) >= 3:
        p1 = df.iloc[-3]
        p2 = df.iloc[-2]
        p3 = df.iloc[-1]
        
        # p1 is strong red
        if p1['Close'] < p1['Open'] and abs(p1['Close'] - p1['Open']) > (p1['High'] - p1['Low']) * 0.5:
            # p2 is a doji/small body (gap down)
            if abs(p2['Close'] - p2['Open']) < (p2['High'] - p2['Low']) * 0.3:
                # p3 is strong green, closing well within p1's body
                if p3['Close'] > p3['Open'] and p3['Close'] > (p1['Open'] + p1['Close']) / 2:
                    patterns_found.append({"pattern_name": "Morning Star", "confidence": 85, "direction": "bullish"})
                    
    # 3. Double Bottom / Double Top (Simplified detection over last 20 bars)
    recent = df.iloc[-20:]
    lows = recent['Low'].values
    highs = recent['High'].values
    
    # Find local minima/maxima
    # A simple heuristic: find lowest points that are separated by at least 5 bars
    minima_idx = np.where((lows[1:-1] < lows[:-2]) & (lows[1:-1] < lows[2:]))[0] + 1
    maxima_idx = np.where((highs[1:-1] > highs[:-2]) & (highs[1:-1] > highs[2:]))[0] + 1
    
    # Double Bottom
    if len(minima_idx) >= 2:
        # Check the last two minima
        m1, m2 = minima_idx[-2], minima_idx[-1]
        if m2 - m1 >= 4: # at least 4 bars apart
            low1, low2 = lows[m1], lows[m2]
            if abs(low1 - low2) / low1 < 0.02: # within 2% of each other
                # Check if current price is breaking out (above the peak between them)
                peak_between = np.max(highs[m1:m2])
                if df.iloc[-1]['Close'] > peak_between * 0.98:
                    patterns_found.append({"pattern_name": "Double Bottom", "confidence": 75, "direction": "bullish"})
                    
    # Double Top
    if len(maxima_idx) >= 2:
        m1, m2 = maxima_idx[-2], maxima_idx[-1]
        if m2 - m1 >= 4:
            high1, high2 = highs[m1], highs[m2]
            if abs(high1 - high2) / high1 < 0.02:
                valley_between = np.min(lows[m1:m2])
                if df.iloc[-1]['Close'] < valley_between * 1.02:
                    patterns_found.append({"pattern_name": "Double Top", "confidence": 75, "direction": "bearish"})

    if not patterns_found:
        return {"pattern_name": "None", "confidence": 0, "direction": "neutral"}
        
    # Return the pattern with highest confidence
    best_pattern = max(patterns_found, key=lambda x: x["confidence"])
    return best_pattern
