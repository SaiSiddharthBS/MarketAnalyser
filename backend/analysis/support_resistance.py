"""
Agent Alpha v6.0 — Support & Resistance Level Detection
======================================================
Calculates dynamic pivot points (local swing highs/lows) to adjust stop loss
and target profit levels relative to actual market structure.
"""
import pandas as pd
import numpy as np
from typing import Tuple, Optional, List

def calculate_pivot_points(df: pd.DataFrame, window: int = 5) -> Tuple[List[float], List[float]]:
    """
    Identify pivot highs (potential resistance) and pivot lows (potential support) in historical data.
    A pivot point is defined as a local extreme over a specified window.
    """
    if df is None or df.empty or len(df) < (window * 2 + 1):
        return [], []
        
    highs = df["High"].values
    lows = df["Low"].values
    
    pivot_highs = []
    pivot_lows = []
    
    for i in range(window, len(df) - window):
        current_high = highs[i]
        current_low = lows[i]
        
        # Check if i is local high
        if all(current_high >= highs[j] for j in range(i - window, i + window + 1) if j != i):
            pivot_highs.append(float(current_high))
            
        # Check if i is local low
        if all(current_low <= lows[j] for j in range(i - window, i + window + 1) if j != i):
            pivot_lows.append(float(current_low))
            
    return pivot_highs, pivot_lows

def get_nearest_levels(df: pd.DataFrame, current_price: float, window: int = 5) -> Tuple[Optional[float], Optional[float]]:
    """
    Find the nearest support level below current_price and nearest resistance level above current_price.
    """
    if df is None or df.empty:
        return None, None
        
    pivot_highs, pivot_lows = calculate_pivot_points(df, window)
    
    # Add recent 20-day high and low as structural extremes
    if len(df) >= 20:
        recent_high = float(df["High"].iloc[-20:].max())
        recent_low = float(df["Low"].iloc[-20:].min())
        pivot_highs.append(recent_high)
        pivot_lows.append(recent_low)
        
    # Also include the 50-day SMA or 200-day SMA as dynamic levels if df has enough rows
    if len(df) >= 50:
        ma50 = float(df["Close"].iloc[-50:].mean())
        if ma50 > current_price:
            pivot_highs.append(ma50)
        else:
            pivot_lows.append(ma50)
            
    # Filter support: levels below current price
    supports = [x for x in pivot_lows if x < current_price and not np.isnan(x)]
    # Filter resistance: levels above current price
    resistances = [x for x in pivot_highs if x > current_price and not np.isnan(x)]
    
    nearest_support = max(supports) if supports else None
    nearest_resistance = min(resistances) if resistances else None
    
    # Round levels to 2 decimal places
    nearest_support = round(nearest_support, 2) if nearest_support is not None else None
    nearest_resistance = round(nearest_resistance, 2) if nearest_resistance is not None else None
    
    return nearest_support, nearest_resistance
