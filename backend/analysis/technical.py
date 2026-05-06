"""
MarketPulse — Technical Analysis Module V3.0
Uses the 'ta' library for indicator calculation + weighted multi-factor scoring.

Scoring Formula (100 points total):
  - Trend Strength (EMA alignment + MACD):  25 points
  - Volume Strength (RVOL):                 20 points
  - RSI / Momentum Quality:                 15 points
  - Sector Strength (vs Nifty 50):          15 points
  - Market Regime (VIX + Nifty trend):      15 points
  - Risk-Reward Ratio:                      10 points

5-Point Signal System:
  80+ = 🚀 STRONG_BUY    | All factors aligned. High conviction.
  60-79 = 🟢 BUY          | Good setup. Most factors positive.
  45-59 = 🟡 WATCH        | Setup forming, not triggered. Monitor.
  25-44 = 🟠 WEAKENING    | Momentum fading. Stock losing strength.
  0-24  = 🔴 EXIT         | Trend broken. No reason to hold or enter.
"""
import pandas as pd
import ta
from datetime import datetime

# Use the shared robust downloader with Yahoo API fallback
from data.stock_fetcher import download_ohlcv


# ─── Cached Market Context (computed once per screener run) ──────

_market_context_cache = {
    "vix": None,
    "nifty_above_50ema": None,
    "regime_score": None,
    "sector_returns": {},
    "timestamp": None,
}


def _fetch_market_context():
    """Fetch VIX + Nifty trend for market regime scoring.
    Cached so we don't re-fetch for every stock in a screener run.
    """
    import time
    now = time.time()

    # Cache for 5 minutes
    if _market_context_cache["timestamp"] and (now - _market_context_cache["timestamp"]) < 300:
        return _market_context_cache

    try:
        # Fetch India VIX
        vix_df = download_ohlcv("^INDIAVIX", period="5d", interval="1d")
        vix_val = float(vix_df["Close"].iloc[-1]) if vix_df is not None and not vix_df.empty else None

        # Fetch Nifty 50 to check if above 50 EMA
        nifty_df = download_ohlcv("^NSEI", period="3mo", interval="1d")
        nifty_above_50ema = False
        if nifty_df is not None and not nifty_df.empty and len(nifty_df) >= 50:
            ema50 = ta.trend.EMAIndicator(close=nifty_df["Close"], window=50).ema_indicator()
            nifty_close = float(nifty_df["Close"].iloc[-1])
            nifty_ema50 = float(ema50.iloc[-1])
            nifty_above_50ema = nifty_close > nifty_ema50

        # Calculate regime score (0-15)
        regime_score = 0
        if vix_val is not None:
            if vix_val < 14:
                regime_score += 10  # Low fear = Risk ON
            elif vix_val < 18:
                regime_score += 7   # Moderate
            elif vix_val < 22:
                regime_score += 4   # Elevated
            else:
                regime_score += 1   # High fear = Risk OFF

        if nifty_above_50ema:
            regime_score += 5  # Nifty in uptrend
        # else: +0 (downtrend)

        regime_score = min(15, regime_score)

        _market_context_cache.update({
            "vix": vix_val,
            "nifty_above_50ema": nifty_above_50ema,
            "regime_score": regime_score,
            "timestamp": now,
        })
    except Exception as e:
        print(f"⚠️ Market context fetch failed: {e}")
        _market_context_cache.update({
            "vix": None,
            "nifty_above_50ema": None,
            "regime_score": 7,  # Neutral fallback
            "timestamp": now,
        })

    return _market_context_cache


def _get_sector_strength(sector_index_yahoo, period_days=10):
    """Calculate sector relative strength vs Nifty 50.
    Returns a score from 0-15.
    """
    cache_key = f"{sector_index_yahoo}_{period_days}"
    if cache_key in _market_context_cache["sector_returns"]:
        return _market_context_cache["sector_returns"][cache_key]

    try:
        sector_df = download_ohlcv(sector_index_yahoo, period="1mo", interval="1d")
        nifty_df = download_ohlcv("^NSEI", period="1mo", interval="1d")

        if sector_df is None or nifty_df is None or len(sector_df) < period_days or len(nifty_df) < period_days:
            _market_context_cache["sector_returns"][cache_key] = 7  # Neutral
            return 7

        sector_ret = (float(sector_df["Close"].iloc[-1]) / float(sector_df["Close"].iloc[-period_days]) - 1) * 100
        nifty_ret = (float(nifty_df["Close"].iloc[-1]) / float(nifty_df["Close"].iloc[-period_days]) - 1) * 100
        relative = sector_ret - nifty_ret

        # Score: how much the sector outperforms Nifty
        if relative > 3:
            score = 15   # Strongly outperforming
        elif relative > 1.5:
            score = 12
        elif relative > 0:
            score = 9    # Slightly outperforming
        elif relative > -1.5:
            score = 6    # Slightly underperforming
        elif relative > -3:
            score = 3
        else:
            score = 0    # Strongly underperforming

        _market_context_cache["sector_returns"][cache_key] = score
        return score

    except Exception as e:
        print(f"⚠️ Sector strength failed for {sector_index_yahoo}: {e}")
        _market_context_cache["sector_returns"][cache_key] = 7
        return 7


# ─── Main Technical Analysis ────────────────────────────────────

def get_technical_analysis(symbol, exchange="NS", period="1y", sector_yahoo_index="^NSEI"):
    """Run full technical analysis on a stock and return indicators + signals.

    Args:
        symbol: Stock symbol (e.g., "RELIANCE")
        exchange: Exchange suffix (e.g., "NS" for NSE)
        period: Data period for analysis
        sector_yahoo_index: Yahoo symbol for the stock's sector index (for sector strength calc)

    Returns:
        Dictionary with score, signal, indicators, entry/target/sl, holding period
    """
    ticker = f"{symbol}.{exchange}" if exchange else symbol
    try:
        df = download_ohlcv(ticker, period=period, interval="1d")
        if df is None or df.empty or len(df) < 50:
            return None
        df = df.reset_index()
    except Exception as e:
        print(f"TA error for {ticker}: {e}")
        return None

    # ─── Calculate Indicators ────────────────────────────────
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

    # ─── RVOL (Relative Volume) ──────────────────────────────
    vol_current = float(latest["Volume"]) if pd.notna(latest["Volume"]) else 0
    vol_20_avg = float(df["Volume"].tail(20).mean()) if len(df) >= 20 else vol_current
    rvol = round(vol_current / vol_20_avg, 2) if vol_20_avg > 0 else 1.0

    # ─── NEW SCORING: Multi-Factor Weighted (0-100) ──────────
    signals = []

    # FACTOR 1: Trend Strength (0-25)
    trend_score = 0
    # EMA alignment (0-15)
    if ema20 and ema50 and ema200:
        if close > ema20 > ema50 > ema200:
            trend_score += 15
            signals.append({"indicator": "EMA", "signal": "STRONG UPTREND (Price > 20 > 50 > 200)", "value": None, "weight": 15})
        elif close > ema50 and close > ema200:
            trend_score += 10
            signals.append({"indicator": "EMA", "signal": "UPTREND (Above 50 & 200 EMA)", "value": None, "weight": 10})
        elif close > ema200:
            trend_score += 5
            signals.append({"indicator": "EMA", "signal": "ABOVE 200 EMA (Long-term bullish)", "value": None, "weight": 5})
        else:
            signals.append({"indicator": "EMA", "signal": "BELOW 200 EMA (Long-term bearish)", "value": None, "weight": 0})

    # MACD (0-10)
    if macd_hist is not None:
        prev_hist = _sf(prev, "MACD_Hist")
        if prev_hist is not None:
            if macd_hist > 0 and prev_hist <= 0:
                trend_score += 10
                signals.append({"indicator": "MACD", "signal": "BULLISH CROSSOVER ✅", "value": macd_hist, "weight": 10})
            elif macd_hist > 0 and macd_hist > prev_hist:
                trend_score += 7
                signals.append({"indicator": "MACD", "signal": "MOMENTUM RISING", "value": macd_hist, "weight": 7})
            elif macd_hist > 0:
                trend_score += 4
                signals.append({"indicator": "MACD", "signal": "POSITIVE BUT SLOWING", "value": macd_hist, "weight": 4})
            elif macd_hist < 0 and prev_hist >= 0:
                trend_score += 0
                signals.append({"indicator": "MACD", "signal": "BEARISH CROSSOVER ❌", "value": macd_hist, "weight": 0})
            else:
                trend_score += 2
                signals.append({"indicator": "MACD", "signal": "NEGATIVE MOMENTUM", "value": macd_hist, "weight": 2})

    # FACTOR 2: Volume Strength (0-20)
    vol_score = 0
    if rvol >= 2.0:
        vol_score = 20
        signals.append({"indicator": "RVOL", "signal": f"VERY HIGH VOLUME ({rvol}x avg)", "value": rvol, "weight": 20})
    elif rvol >= 1.5:
        vol_score = 16
        signals.append({"indicator": "RVOL", "signal": f"HIGH VOLUME ({rvol}x avg)", "value": rvol, "weight": 16})
    elif rvol >= 1.0:
        vol_score = 12
        signals.append({"indicator": "RVOL", "signal": f"ABOVE AVERAGE ({rvol}x avg)", "value": rvol, "weight": 12})
    elif rvol >= 0.7:
        vol_score = 6
        signals.append({"indicator": "RVOL", "signal": f"BELOW AVERAGE ({rvol}x avg)", "value": rvol, "weight": 6})
    else:
        vol_score = 2
        signals.append({"indicator": "RVOL", "signal": f"LOW VOLUME ({rvol}x avg)", "value": rvol, "weight": 2})

    # FACTOR 3: RSI / Momentum Quality (0-15)
    rsi_score = 0
    if rsi is not None:
        if 30 <= rsi < 40:
            rsi_score = 15  # Oversold bounce zone — best entry
            signals.append({"indicator": "RSI", "signal": f"OVERSOLD BOUNCE ZONE ({rsi:.0f})", "value": rsi, "weight": 15})
        elif 50 <= rsi < 60:
            rsi_score = 12  # Bullish momentum
            signals.append({"indicator": "RSI", "signal": f"BULLISH MOMENTUM ({rsi:.0f})", "value": rsi, "weight": 12})
        elif 40 <= rsi < 50:
            rsi_score = 10  # Approaching bullish
            signals.append({"indicator": "RSI", "signal": f"NEUTRAL-BULLISH ({rsi:.0f})", "value": rsi, "weight": 10})
        elif 60 <= rsi < 70:
            rsi_score = 8   # Strong but getting hot
            signals.append({"indicator": "RSI", "signal": f"STRONG MOMENTUM ({rsi:.0f})", "value": rsi, "weight": 8})
        elif rsi < 30:
            rsi_score = 5   # Deeply oversold — risky
            signals.append({"indicator": "RSI", "signal": f"DEEPLY OVERSOLD ({rsi:.0f}) ⚠️", "value": rsi, "weight": 5})
        elif 70 <= rsi < 80:
            rsi_score = 3   # Overbought
            signals.append({"indicator": "RSI", "signal": f"OVERBOUGHT ({rsi:.0f})", "value": rsi, "weight": 3})
        else:
            rsi_score = 0   # Extremely overbought
            signals.append({"indicator": "RSI", "signal": f"EXTREMELY OVERBOUGHT ({rsi:.0f}) 🔴", "value": rsi, "weight": 0})

    # FACTOR 4: Sector Strength (0-15)
    sector_score = _get_sector_strength(sector_yahoo_index)
    signals.append({"indicator": "Sector", "signal": f"Sector strength vs Nifty: {sector_score}/15", "value": sector_score, "weight": sector_score})

    # FACTOR 5: Market Regime (0-15)
    ctx = _fetch_market_context()
    regime_score = ctx.get("regime_score", 7)
    vix_display = f"VIX: {ctx['vix']:.1f}" if ctx.get("vix") else "VIX: N/A"
    nifty_trend = "Above 50 EMA" if ctx.get("nifty_above_50ema") else "Below 50 EMA"
    signals.append({"indicator": "Market", "signal": f"Regime: {vix_display}, Nifty {nifty_trend} ({regime_score}/15)", "value": regime_score, "weight": regime_score})

    # FACTOR 6: Risk-Reward Ratio (0-10) — DYNAMIC multipliers
    entry = close
    # Determine target/SL multipliers based on trend strength
    trend_strength = trend_score / 25.0  # 0.0 to 1.0
    sl_mult = 1.5 + (0.5 * (1 - trend_strength))  # Weak trend = wider SL (2.0), Strong = tighter (1.5)
    tgt_mult = 2.0 + (2.5 * trend_strength)        # Weak trend = modest target (2.0x), Strong = aggressive (4.5x)

    sl = round(close - (sl_mult * atr_val), 2) if atr_val else round(close * 0.97, 2)
    target = round(close + (tgt_mult * atr_val), 2) if atr_val else round(close * 1.05, 2)
    rr_ratio = round((target - entry) / (entry - sl), 2) if entry > sl else 0

    rr_score = 0
    if rr_ratio >= 3.0:
        rr_score = 10
    elif rr_ratio >= 2.5:
        rr_score = 8
    elif rr_ratio >= 2.0:
        rr_score = 6
    elif rr_ratio >= 1.5:
        rr_score = 4
    else:
        rr_score = 2
    signals.append({"indicator": "R/R", "signal": f"Risk-Reward: {rr_ratio}:1", "value": rr_ratio, "weight": rr_score})

    # ─── TOTAL SCORE ─────────────────────────────────────────
    score = trend_score + vol_score + rsi_score + sector_score + regime_score + rr_score
    score = max(0, min(100, score))

    # Additional context signals (informational, don't affect score)
    # Bollinger Band position
    if bb_upper and bb_lower and (bb_upper - bb_lower) > 0:
        bb_pct = round((close - bb_lower) / (bb_upper - bb_lower), 2)
        if bb_pct < 0.1:
            signals.append({"indicator": "Bollinger", "signal": "AT LOWER BAND — Oversold zone", "value": bb_pct, "weight": 0})
        elif bb_pct > 0.9:
            signals.append({"indicator": "Bollinger", "signal": "AT UPPER BAND — Overbought zone", "value": bb_pct, "weight": 0})

    # ADX trend strength
    if adx is not None:
        if adx > 25:
            signals.append({"indicator": "ADX", "signal": f"STRONG TREND ({adx:.0f})", "value": adx, "weight": 0})
        else:
            signals.append({"indicator": "ADX", "signal": f"WEAK/NO TREND ({adx:.0f})", "value": adx, "weight": 0})

    # ─── Contextual Phase Engine ─────────────────────────────
    # Calculate explicit Risk/Reward percentages
    reward_pct = round(((target - entry) / entry) * 100, 2) if entry > 0 else 0
    risk_pct = round(((entry - sl) / entry) * 100, 2) if entry > 0 else 0

    _rsi = rsi if rsi is not None else 50
    _rvol = rvol if rvol is not None else 1.0

    # Phase Logic
    if score >= 60 and 50 <= _rsi <= 66 and _rvol >= 1.2 and close > (ema50 or 0):
        overall = "EARLY_MOMENTUM"
        signals.append({"indicator": "Phase", "signal": "Early Breakout. Fresh momentum.", "value": _rsi, "weight": 0})
    elif score >= 65 and 66 < _rsi <= 72 and _rvol >= 1.2 and close > (ema20 or 0):
        overall = "CONTINUATION"
        signals.append({"indicator": "Phase", "signal": "Strong Continuation. Trend active.", "value": _rsi, "weight": 0})
    elif score >= 60 and (_rsi > 72 or (_rsi > 68 and _rvol < 1.0)):
        overall = "EXTENDED"
        score -= 15  # Penalize extended setups so early ones rank higher
        score = max(0, score)
        signals.append({"indicator": "Phase Warning", "signal": "Extended momentum. High pullback risk.", "value": _rsi, "weight": 0})
    elif 45 <= score < 65 and 40 <= _rsi <= 55 and (close >= (ema50 or close) * 0.98):
        overall = "PULLBACK"
        signals.append({"indicator": "Phase", "signal": "Resting at support. Watch for bounce.", "value": _rsi, "weight": 0})
    elif 30 <= score < 45:
        overall = "WEAK"
        signals.append({"indicator": "Phase Warning", "signal": "Losing momentum. Weak setup.", "value": _rsi, "weight": 0})
    else:
        overall = "AVOID"

    # ─── Holding Period Estimate (ATR-based, swing-calibrated) ─
    holding_sessions_low = 0
    holding_sessions_high = 0
    holding_label = "N/A"
    if atr_val and atr_val > 0:
        # A stock captures ~40% of ATR per day on average in a trend
        daily_capture = 0.4
        target_distance = abs(target - entry)
        base_sessions = target_distance / (atr_val * daily_capture)
        holding_sessions_low = max(3, int(base_sessions * 0.7))
        holding_sessions_high = max(holding_sessions_low + 2, int(base_sessions * 1.4))
        if holding_sessions_high <= 8:
            holding_label = f"⚡ {holding_sessions_low}–{holding_sessions_high} trading days"
        elif holding_sessions_high <= 20:
            low_wk = max(1, holding_sessions_low // 5)
            high_wk = max(low_wk + 1, (holding_sessions_high + 4) // 5)
            holding_label = f"🕒 {low_wk}–{high_wk} weeks"
        elif holding_sessions_high <= 45:
            low_wk = max(2, holding_sessions_low // 5)
            high_wk = max(low_wk + 1, (holding_sessions_high + 4) // 5)
            holding_label = f"📅 {low_wk}–{high_wk} weeks"
        else:
            low_mo = max(1, holding_sessions_low // 22)
            high_mo = max(low_mo + 1, (holding_sessions_high + 21) // 22)
            holding_label = f"🐢 {low_mo}–{high_mo} months"

    # ─── ATR-Based Predicted Range (Next Day) ──────────────
    pred_high = round(close + atr_val, 2) if atr_val else None
    pred_low = round(close - atr_val, 2) if atr_val else None
    # Support/Resistance
    support = round(min(filter(None, [ema50, ema200, bb_lower, sl])), 2) if any([ema50, ema200, bb_lower]) else sl
    resistance = round(max(filter(None, [bb_upper, target])), 2) if bb_upper else target

    # Recommended quantity (₹5L capital, 1% risk)
    risk_per_share = entry - sl if sl else 0
    rec_qty = int((500000 * 0.01) / risk_per_share) if risk_per_share > 0 else 0

    return {
        "symbol": symbol,
        "price": round(close, 2),
        "score": score,
        "signal": overall,
        "entry": round(entry, 2),
        "target": target,
        "stop_loss": sl,
        "risk_reward": rr_ratio,
        "reward_pct": reward_pct,
        "risk_pct": risk_pct,
        "rvol": rvol,
        "rec_qty": rec_qty,
        # Score breakdown
        "score_breakdown": {
            "trend": trend_score,
            "volume": vol_score,
            "rsi": rsi_score,
            "sector": sector_score,
            "regime": regime_score,
            "risk_reward": rr_score,
        },
        # Holding period
        "holding_period": holding_label,
        "holding_sessions": f"{holding_sessions_low}–{holding_sessions_high} sessions",
        # Predicted range
        "predicted_range": {
            "high": pred_high,
            "low": pred_low,
            "support": support,
            "resistance": resistance,
        },
        # Indicators
        "indicators": {
            "rsi": rsi, "macd": macd_val, "macd_signal": macd_signal,
            "macd_histogram": macd_hist, "bb_upper": bb_upper, "bb_mid": bb_mid,
            "bb_lower": bb_lower, "ema_20": ema20, "ema_50": ema50,
            "ema_200": ema200, "atr": atr_val, "adx": adx,
            "stoch_k": stoch_k, "stoch_d": stoch_d, "rvol": rvol,
        },
        "signals": signals,
        # Market context
        "market_regime": {
            "vix": ctx.get("vix"),
            "nifty_trend": "bullish" if ctx.get("nifty_above_50ema") else "bearish",
            "regime_score": regime_score,
        },
    }


# ─── Screener ────────────────────────────────────────────────────

def screen_stocks(symbols, exchange="NS", top_n=10, sector_yahoo_index="^NSEI"):
    """Screen multiple stocks and return top N by score. Deduplicates by symbol."""
    results = []
    seen_symbols = set()
    for sym in symbols:
        if sym in seen_symbols:
            continue  # Skip duplicate symbols
        seen_symbols.add(sym)
        try:
            analysis = get_technical_analysis(sym, exchange, sector_yahoo_index=sector_yahoo_index)
            if analysis:
                results.append(analysis)
        except Exception as e:
            print(f"Screener error for {sym}: {e}")
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_n]


# ─── Utility ─────────────────────────────────────────────────────

def _sf(row, col):
    """Safely extract a float value."""
    try:
        val = row.get(col) if isinstance(row, dict) else row[col] if col in row.index else None
        if val is not None and pd.notna(val):
            return round(float(val), 2)
    except (KeyError, TypeError, ValueError):
        pass
    return None
