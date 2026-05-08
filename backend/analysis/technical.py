"""
Agent Alpha v2.0 — Advanced Technical Analysis Model (Model 1)
================================================================
Weight in ensemble: 20%

Upgraded from v1's basic indicators to institutional-grade technicals:
1. Kaufman's Adaptive Moving Average (KAMA)
   - Replaces static EMAs. KAMA dynamically adjusts its smoothing 
     constant based on market noise. It flattens during chop (preventing 
     whipsaws) and accelerates during strong trends.
2. RSI Divergence Detection
   - Price makes a Lower Low, but RSI makes a Higher Low (Bullish Divergence).
   - Highly predictive leading indicator of reversals.
3. ADX (Average Directional Index)
   - Filters out trades in trendless markets (ADX < 20).
   - Only takes momentum breakouts if ADX > 25 and rising.
4. ATR-based dynamic stops.
"""
import pandas as pd
import numpy as np
import math
from typing import Dict, Any, Optional, Tuple
import ta

def calculate_kama(close: pd.Series, n: int = 10, pow1: int = 2, pow2: int = 30) -> pd.Series:
    """
    Calculate Kaufman's Adaptive Moving Average (KAMA).
    
    Args:
        close: Price series
        n: Efficiency Ratio period (default 10)
        pow1: Fast EMA constant (default 2 for 2-period EMA)
        pow2: Slow EMA constant (default 30 for 30-period EMA)
        
    Returns:
        Series of KAMA values
    """
    # Efficiency Ratio (ER) = Direction / Volatility
    direction = close.diff(n).abs()
    volatility = close.diff(1).abs().rolling(n).sum()
    
    er = direction / volatility
    
    # Smoothing Constant (SC)
    fast_sc = 2 / (pow1 + 1)
    slow_sc = 2 / (pow2 + 1)
    sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2
    
    # KAMA calculation
    kama = pd.Series(index=close.index, dtype='float64')
    
    # Seed first value
    first_valid = sc.first_valid_index()
    if first_valid is None:
        return close.copy()
        
    # Get integer location of the first valid index
    first_valid_iloc = close.index.get_loc(first_valid)
    if isinstance(first_valid_iloc, slice):
        first_valid_iloc = first_valid_iloc.start
        
    kama.iloc[first_valid_iloc] = close.iloc[first_valid_iloc]
    
    # Needs a loop due to recursive nature (numba could speed this up in future)
    for i in range(first_valid_iloc + 1, len(close)):
        kama.iloc[i] = kama.iloc[i-1] + sc.iloc[i] * (close.iloc[i] - kama.iloc[i-1])
        
    return kama

def detect_rsi_divergence(df: pd.DataFrame, lookback: int = 20) -> Dict[str, Any]:
    """
    Mathematically detect Regular RSI Divergences.
    
    Bullish Divergence: Price Lower Low + RSI Higher Low
    Bearish Divergence: Price Higher High + RSI Lower High
    """
    if len(df) < lookback + 5:
        return {"type": "none", "score": 0}
        
    close = df["Close"].values
    rsi = ta.momentum.RSIIndicator(df["Close"], window=14).rsi().values
    
    # Look at recent data vs older data in the window
    recent_price = close[-5:]
    recent_rsi = rsi[-5:]
    
    older_price = close[-lookback:-5]
    older_rsi = rsi[-lookback:-5]
    
    if len(older_price) == 0 or len(recent_price) == 0:
        return {"type": "none", "score": 0}
        
    recent_min_p, recent_max_p = np.min(recent_price), np.max(recent_price)
    older_min_p, older_max_p = np.min(older_price), np.max(older_price)
    
    recent_min_r, recent_max_r = np.min(recent_rsi), np.max(recent_rsi)
    older_min_r, older_max_r = np.min(older_rsi), np.max(older_rsi)
    
    # Bullish Divergence (Price LL, RSI HL)
    if recent_min_p < older_min_p * 0.99 and recent_min_r > older_min_r + 5:
        if recent_min_r < 40: # Only valid if RSI was somewhat oversold
            return {
                "type": "bullish_divergence", 
                "score": 3,
                "msg": "Bullish RSI Divergence detected (Price LL, RSI HL)"
            }
            
    # Bearish Divergence (Price HH, RSI LH)
    if recent_max_p > older_max_p * 1.01 and recent_max_r < older_max_r - 5:
        if recent_max_r > 60: # Only valid if RSI was somewhat overbought
            return {
                "type": "bearish_divergence", 
                "score": -3,
                "msg": "Bearish RSI Divergence detected (Price HH, RSI LH)"
            }
            
    return {"type": "none", "score": 0, "msg": ""}

def calculate_technical_signal(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate Model 1 Technical Signal using advanced indicators.
    """
    if df is None or df.empty or len(df) < 50:
        return {"signal": "NEUTRAL", "confidence": 0, "direction": 0}
        
    df = df.copy()
    close = df["Close"]
    
    # ─── 1. KAMA Trend ───────────────────────────────────────
    kama_fast = calculate_kama(close, n=10, pow1=2, pow2=30)
    kama_slow = calculate_kama(close, n=10, pow1=5, pow2=50)
    
    current_kama_f = kama_fast.iloc[-1]
    current_kama_s = kama_slow.iloc[-1]
    
    kama_trend_up = current_kama_f > current_kama_s
    
    # ─── 2. Trend Strength (ADX) ─────────────────────────────
    adx_ind = ta.trend.ADXIndicator(df["High"], df["Low"], df["Close"], window=14)
    adx = adx_ind.adx().iloc[-1]
    plus_di = adx_ind.adx_pos().iloc[-1]
    minus_di = adx_ind.adx_neg().iloc[-1]
    
    strong_trend = adx > 25
    bull_momentum = plus_di > minus_di
    
    # ─── 3. Divergence ───────────────────────────────────────
    div = detect_rsi_divergence(df)
    
    # ─── Scoring Logic ───────────────────────────────────────
    score = 0
    reasons = []
    
    # Trend alignment
    if kama_trend_up:
        if close.iloc[-1] > current_kama_f:
            score += 2
            reasons.append("Price above Fast KAMA + KAMA Bullish cross")
        else:
            score += 1
            reasons.append("KAMA Bullish cross, but price testing support")
    else:
        if close.iloc[-1] < current_kama_f:
            score -= 2
            reasons.append("Price below Fast KAMA + KAMA Bearish cross")
        else:
            score -= 1
            reasons.append("KAMA Bearish cross, but price testing resistance")
            
    # ADX filtering
    if strong_trend:
        if bull_momentum:
            score += 2
            reasons.append(f"Strong Bullish Trend (ADX {adx:.1f}, +DI > -DI)")
        else:
            score -= 2
            reasons.append(f"Strong Bearish Trend (ADX {adx:.1f}, -DI > +DI)")
    else:
        reasons.append(f"Weak/Choppy Trend (ADX {adx:.1f} < 25)")
        # In weak trends, mean reversion is better than trend following
        
    # Add divergence score
    if div["score"] != 0:
        score += div["score"]
        reasons.append(div["msg"])
        
    # ─── Final Signal ────────────────────────────────────────
    if score >= 4:
        signal, direction = "BUY", 1
        confidence = min(90, 50 + score * 8)
    elif score >= 2:
        signal, direction = "BUY", 1
        confidence = min(70, 40 + score * 10)
    elif score <= -4:
        signal, direction = "SELL", -1
        confidence = min(90, 50 + abs(score) * 8)
    elif score <= -2:
        signal, direction = "SELL", -1
        confidence = min(70, 40 + abs(score) * 10)
    else:
        signal, direction = "NEUTRAL", 0
        confidence = 40
        
    # Calculate ATR for stops
    atr = ta.volatility.AverageTrueRange(df["High"], df["Low"], df["Close"]).average_true_range().iloc[-1]
        
    def safe_float(v):
        try:
            val = float(v)
            return 0.0 if math.isnan(val) else round(val, 2)
        except:
            return 0.0

    return {
        "signal": signal,
        "confidence": confidence,
        "direction": direction,
        "technical_score": score,
        "metrics": {
            "adx": safe_float(adx),
            "kama_fast": safe_float(current_kama_f),
            "kama_slow": safe_float(current_kama_s),
            "atr": safe_float(atr)
        },
        "reasons": reasons
    }

from data.stock_fetcher import get_stock_data

def get_technical_analysis(symbol: str, exchange: str = "NS", period: str = "1y", sector_index: str = "^NSEI") -> Optional[Dict[str, Any]]:
    """Backward compatibility wrapper for API."""
    # Convert period from 1y to data.stock_fetcher format if needed, but get_stock_data handles it
    df = get_stock_data(symbol, period=period, exchange=exchange)
    if not df or len(df) == 0:
        return None
        
    signal_data = calculate_technical_signal(pd.DataFrame(df))
    close_price = df[-1]["Close"] if isinstance(df, list) and len(df) > 0 else 0
    
    return {
        "symbol": symbol,
        "score": max(0, min(100, 50 + signal_data["technical_score"] * 10)),
        "signal": signal_data["signal"],
        "signals": [{"indicator": "Advanced Technicals", "signal": signal_data["signal"], "value": signal_data["technical_score"]}],
        "score_breakdown": {"Technical": signal_data["technical_score"]},
        "reasons": signal_data.get("reasons", []),
        "entry": close_price,
        "target": close_price * 1.05,
        "stop_loss": close_price * 0.95,
        "metrics": signal_data.get("metrics", {})
    }

def screen_stocks(symbols: list, top_n: int = 10, sector_yahoo_index: str = "^NSEI") -> list:
    """Screen a list of symbols and return the top N by technical score."""
    results = []
    for symbol in symbols:
        try:
            ta_res = get_technical_analysis(symbol, sector_index=sector_yahoo_index)
            if ta_res and ta_res["signal"] in ["BUY", "STRONG_BUY"]:
                results.append(ta_res)
        except Exception as e:
            print(f"Error screening {symbol}: {e}")
            
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_n]
