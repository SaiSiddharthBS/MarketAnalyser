"""
MarketPulse — Technical Analysis Module
Uses the 'ta' library for indicator calculation + custom signal logic.
"""
import pandas as pd
import ta
import yfinance as yf

# Use the shared robust downloader with Yahoo API fallback
from data.stock_fetcher import download_ohlcv


def get_technical_analysis(symbol, exchange="NS", period="1y"):
    """Run full technical analysis on a stock and return indicators + signals."""
    ticker = f"{symbol}.{exchange}" if exchange else symbol
    try:
        df = download_ohlcv(ticker, period=period, interval="1d")
        if df is None or df.empty or len(df) < 50:
            return None
        df = df.reset_index()
    except Exception as e:
        print(f"TA error for {ticker}: {e}")
        return None

    # Calculate indicators using 'ta' library
    # RSI
    df["RSI_14"] = ta.momentum.RSIIndicator(close=df["Close"], window=14).rsi()
    # MACD
    macd_ind = ta.trend.MACD(close=df["Close"], window_slow=26, window_fast=12, window_sign=9)
    df["MACD"] = macd_ind.macd()
    df["MACD_Signal"] = macd_ind.macd_signal()
    df["MACD_Hist"] = macd_ind.macd_diff()
    # Bollinger Bands
    bb = ta.volatility.BollingerBands(close=df["Close"], window=20, window_dev=2)
    df["BB_Upper"] = bb.bollinger_hband()
    df["BB_Mid"] = bb.bollinger_mavg()
    df["BB_Lower"] = bb.bollinger_lband()
    # EMAs
    df["EMA_20"] = ta.trend.EMAIndicator(close=df["Close"], window=20).ema_indicator()
    df["EMA_50"] = ta.trend.EMAIndicator(close=df["Close"], window=50).ema_indicator()
    df["EMA_200"] = ta.trend.EMAIndicator(close=df["Close"], window=200).ema_indicator()
    # ATR
    df["ATR"] = ta.volatility.AverageTrueRange(high=df["High"], low=df["Low"], close=df["Close"], window=14).average_true_range()
    # ADX
    adx_ind = ta.trend.ADXIndicator(high=df["High"], low=df["Low"], close=df["Close"], window=14)
    df["ADX"] = adx_ind.adx()
    # Stochastic
    stoch = ta.momentum.StochasticOscillator(high=df["High"], low=df["Low"], close=df["Close"], window=14, smooth_window=3)
    df["Stoch_K"] = stoch.stoch()
    df["Stoch_D"] = stoch.stoch_signal()
    # OBV
    df["OBV"] = ta.volume.OnBalanceVolumeIndicator(close=df["Close"], volume=df["Volume"]).on_balance_volume()

    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest

    close = float(latest["Close"])
    rsi = _sf(latest, "RSI_14")
    macd_val = _sf(latest, "MACD")
    macd_signal = _sf(latest, "MACD_Signal")
    macd_hist = _sf(latest, "MACD_Hist")
    bb_upper = _sf(latest, "BB_Upper")
    bb_lower = _sf(latest, "BB_Lower")
    bb_mid = _sf(latest, "BB_Mid")
    ema20 = _sf(latest, "EMA_20")
    ema50 = _sf(latest, "EMA_50")
    ema200 = _sf(latest, "EMA_200")
    atr_val = _sf(latest, "ATR")
    adx = _sf(latest, "ADX")
    stoch_k = _sf(latest, "Stoch_K")
    stoch_d = _sf(latest, "Stoch_D")

    # Generate signals & composite score
    signals = []
    score = 50  # Neutral start

    # RSI
    if rsi is not None:
        if rsi < 30:
            signals.append({"indicator": "RSI", "signal": "OVERSOLD — Potential bounce", "value": rsi, "weight": 15})
            score += 15
        elif rsi < 40:
            signals.append({"indicator": "RSI", "signal": "APPROACHING OVERSOLD", "value": rsi, "weight": 8})
            score += 8
        elif rsi > 70:
            signals.append({"indicator": "RSI", "signal": "OVERBOUGHT — Caution", "value": rsi, "weight": -15})
            score -= 15
        elif rsi > 60:
            signals.append({"indicator": "RSI", "signal": "APPROACHING OVERBOUGHT", "value": rsi, "weight": -5})
            score -= 5
        else:
            signals.append({"indicator": "RSI", "signal": "NEUTRAL", "value": rsi, "weight": 0})

    # MACD
    if macd_hist is not None:
        prev_hist = _sf(prev, "MACD_Hist")
        if prev_hist is not None:
            if macd_hist > 0 and prev_hist <= 0:
                signals.append({"indicator": "MACD", "signal": "BULLISH CROSSOVER ✅", "value": macd_hist, "weight": 12})
                score += 12
            elif macd_hist < 0 and prev_hist >= 0:
                signals.append({"indicator": "MACD", "signal": "BEARISH CROSSOVER ❌", "value": macd_hist, "weight": -12})
                score -= 12
            elif macd_hist > prev_hist:
                signals.append({"indicator": "MACD", "signal": "MOMENTUM RISING", "value": macd_hist, "weight": 5})
                score += 5
            else:
                signals.append({"indicator": "MACD", "signal": "MOMENTUM FALLING", "value": macd_hist, "weight": -5})
                score -= 5

    # EMA trend
    if ema20 and ema50 and ema200:
        if close > ema20 > ema50 > ema200:
            signals.append({"indicator": "EMA", "signal": "STRONG UPTREND (Price > 20 > 50 > 200)", "value": None, "weight": 15})
            score += 15
        elif close < ema20 < ema50 < ema200:
            signals.append({"indicator": "EMA", "signal": "STRONG DOWNTREND", "value": None, "weight": -15})
            score -= 15
        elif close > ema200:
            signals.append({"indicator": "EMA", "signal": "ABOVE 200 EMA (Long-term bullish)", "value": None, "weight": 5})
            score += 5
        else:
            signals.append({"indicator": "EMA", "signal": "BELOW 200 EMA (Long-term bearish)", "value": None, "weight": -5})
            score -= 5

    # Bollinger Bands
    if bb_upper and bb_lower and (bb_upper - bb_lower) > 0:
        bb_pct = (close - bb_lower) / (bb_upper - bb_lower)
        if bb_pct < 0.1:
            signals.append({"indicator": "Bollinger", "signal": "AT LOWER BAND — Oversold zone", "value": round(bb_pct, 2), "weight": 10})
            score += 10
        elif bb_pct > 0.9:
            signals.append({"indicator": "Bollinger", "signal": "AT UPPER BAND — Overbought zone", "value": round(bb_pct, 2), "weight": -10})
            score -= 10

    # ADX trend strength
    if adx is not None:
        if adx > 25:
            signals.append({"indicator": "ADX", "signal": f"STRONG TREND ({adx:.0f})", "value": adx, "weight": 0})
        else:
            signals.append({"indicator": "ADX", "signal": f"WEAK/NO TREND ({adx:.0f})", "value": adx, "weight": 0})

    # Clamp score
    score = max(0, min(100, score))

    # Overall signal
    if score >= 75:
        overall = "STRONG_BUY"
    elif score >= 60:
        overall = "BUY"
    elif score >= 40:
        overall = "HOLD"
    elif score >= 25:
        overall = "SELL"
    else:
        overall = "STRONG_SELL"

    # Entry/Target/SL using ATR
    entry = close
    sl = round(close - (2 * atr_val), 2) if atr_val else round(close * 0.97, 2)
    target = round(close + (3 * atr_val), 2) if atr_val else round(close * 1.05, 2)

    return {
        "symbol": symbol,
        "price": round(close, 2),
        "score": score,
        "signal": overall,
        "entry": round(entry, 2),
        "target": target,
        "stop_loss": sl,
        "risk_reward": round((target - entry) / (entry - sl), 2) if entry != sl else 0,
        "indicators": {
            "rsi": rsi, "macd": macd_val, "macd_signal": macd_signal,
            "macd_histogram": macd_hist, "bb_upper": bb_upper, "bb_mid": bb_mid,
            "bb_lower": bb_lower, "ema_20": ema20, "ema_50": ema50,
            "ema_200": ema200, "atr": atr_val, "adx": adx,
            "stoch_k": stoch_k, "stoch_d": stoch_d,
        },
        "signals": signals,
    }


def screen_stocks(symbols, exchange="NS", top_n=10):
    """Screen multiple stocks and return top N by score."""
    results = []
    for sym in symbols:
        try:
            analysis = get_technical_analysis(sym, exchange)
            if analysis:
                results.append(analysis)
        except Exception as e:
            print(f"Screener error for {sym}: {e}")
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_n]


def _sf(row, col):
    """Safely extract a float value."""
    try:
        val = row.get(col) if isinstance(row, dict) else row[col] if col in row.index else None
        if val is not None and pd.notna(val):
            return round(float(val), 2)
    except (KeyError, TypeError, ValueError):
        pass
    return None
