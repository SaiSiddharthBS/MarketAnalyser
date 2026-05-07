import pandas as pd
import ta
from datetime import datetime, timedelta
from data.stock_fetcher import download_ohlcv

def calculate_daily_regime(nifty_close, nifty_ema20, nifty_ema50, vix_close):
    """Calculate the raw market regime for a single day based on technicals."""
    if vix_close > 22:
        return "HIGH_VOLATILITY"
    
    if nifty_close > nifty_ema20 and nifty_close > nifty_ema50:
        return "BULLISH_TREND"
    elif nifty_close < nifty_ema20 and nifty_close < nifty_ema50:
        return "BEARISH"
    elif nifty_close < nifty_ema20 and nifty_close > nifty_ema50:
        return "PULLBACK"
    else:
        return "SIDEWAYS"

def get_smoothed_market_regime():
    """
    Get the market regime with a 3-day persistence rule.
    If the raw regime has been the same for the last 3 days, that becomes the smoothed regime.
    Otherwise, it returns the last established smoothed regime.
    """
    try:
        # Fetch last 15 days to ensure we have enough trading days
        nifty_df = download_ohlcv("^NSEI", period="1mo", interval="1d")
        vix_df = download_ohlcv("^INDIAVIX", period="1mo", interval="1d")
        
        if nifty_df is None or nifty_df.empty or vix_df is None or vix_df.empty:
            return {"regime": "UNKNOWN", "message": "Failed to fetch market data."}
            
        # Calculate EMAs for NIFTY
        nifty_df["EMA20"] = ta.trend.EMAIndicator(close=nifty_df["Close"], window=20).ema_indicator()
        nifty_df["EMA50"] = ta.trend.EMAIndicator(close=nifty_df["Close"], window=50).ema_indicator()
        
        # Merge NIFTY and VIX on date
        # yfinance index is datetime
        nifty_df = nifty_df.dropna(subset=["EMA50"])
        
        raw_regimes = []
        for i in range(len(nifty_df)):
            date = nifty_df.index[i]
            n_close = nifty_df["Close"].iloc[i]
            n_ema20 = nifty_df["EMA20"].iloc[i]
            n_ema50 = nifty_df["EMA50"].iloc[i]
            
            # Find matching VIX
            vix_row = vix_df[vix_df.index == date]
            if vix_row.empty:
                v_close = 15.0 # default fallback
            else:
                v_close = vix_row["Close"].iloc[0]
                
            raw = calculate_daily_regime(n_close, n_ema20, n_ema50, v_close)
            raw_regimes.append(raw)
            
        if len(raw_regimes) < 3:
            return {"regime": "UNKNOWN", "message": "Insufficient data for regime detection."}
            
        # Apply 3-day smoothing
        # We look back from the end. 
        # The smoothed regime only changes if the raw regime is identical for 3 consecutive days.
        smoothed_regime = raw_regimes[0] # start with oldest available
        
        for i in range(2, len(raw_regimes)):
            # Check if last 3 days are the same
            if raw_regimes[i] == raw_regimes[i-1] == raw_regimes[i-2]:
                smoothed_regime = raw_regimes[i]
                
        current_vix = float(vix_df["Close"].iloc[-1]) if not vix_df.empty else 0
        current_nifty = float(nifty_df["Close"].iloc[-1])
        
        # Construct message and colors
        messages = {
            "BULLISH_TREND": "Favorable for Early Breakouts and Momentum trades.",
            "BEARISH": "Defensive mode. Cash is a position. Avoid aggressive buying.",
            "SIDEWAYS": "Range-bound market. Focus on pullbacks and mean reversion.",
            "PULLBACK": "Market dipping in an uptrend. Watch for support bounces.",
            "HIGH_VOLATILITY": "Fear is elevated (VIX > 22). Reduce position sizes immediately.",
            "UNKNOWN": "Market context unavailable."
        }
        
        colors = {
            "BULLISH_TREND": "#10b981", # Green
            "PULLBACK": "#3b82f6",      # Blue
            "SIDEWAYS": "#f59e0b",      # Orange
            "BEARISH": "#ef4444",       # Red
            "HIGH_VOLATILITY": "#9333ea", # Purple
            "UNKNOWN": "#6b7280"        # Gray
        }
        
        emojis = {
            "BULLISH_TREND": "🟢",
            "PULLBACK": "📉",
            "SIDEWAYS": "🟡",
            "BEARISH": "🔴",
            "HIGH_VOLATILITY": "⚡",
            "UNKNOWN": "⚪"
        }
        
        vix_level = "Calm" if current_vix < 15 else "Elevated" if current_vix < 20 else "High Fear"
        nifty_trend = "Uptrend" if current_nifty > n_ema50 else "Downtrend"
        
        return {
            "regime": smoothed_regime,
            "status": smoothed_regime.replace("_", " "),
            "color": colors.get(smoothed_regime, "#6b7280"),
            "emoji": emojis.get(smoothed_regime, "⚪"),
            "raw_today": raw_regimes[-1],
            "vix": round(current_vix, 2),
            "vix_level": vix_level,
            "nifty": round(current_nifty, 2),
            "nifty_trend": nifty_trend,
            "message": messages.get(smoothed_regime, "")
        }
        
    except Exception as e:
        print(f"Error calculating market regime: {e}")
        return {"status": "UNKNOWN", "color": "#6b7280", "emoji": "⚪"}
