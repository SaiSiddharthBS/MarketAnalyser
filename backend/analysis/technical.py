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
    
    # ─── 1. KAMA Trend (Daily) ───────────────────────────────
    kama_fast = calculate_kama(close, n=10, pow1=2, pow2=30)
    kama_slow = calculate_kama(close, n=10, pow1=5, pow2=50)
    
    current_kama_f = kama_fast.iloc[-1]
    current_kama_s = kama_slow.iloc[-1]
    
    kama_trend_up = current_kama_f > current_kama_s
    
    # ─── Task 24: MTF Confirmation (Weekly) ──────────────────
    try:
        mtf_df = df.copy()
        mtf_df['Date'] = pd.to_datetime(mtf_df['Date'])
        mtf_df.set_index('Date', inplace=True)
        weekly_df = mtf_df.resample('W').agg({
            'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
        }).dropna()
        if len(weekly_df) > 10:
            weekly_kama_f = calculate_kama(weekly_df["Close"], n=10, pow1=2, pow2=30).iloc[-1]
            weekly_kama_s = calculate_kama(weekly_df["Close"], n=10, pow1=5, pow2=50).iloc[-1]
            weekly_trend_up = weekly_kama_f > weekly_kama_s
        else:
            weekly_trend_up = kama_trend_up # Fallback
    except Exception as e:
        weekly_trend_up = kama_trend_up # Fallback on error
    
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
            reasons.append("Price above Fast KAMA + Daily Bullish cross")
        else:
            score += 1
            reasons.append("Daily Bullish cross, but price testing support")
            
        if weekly_trend_up:
            score += 2
            reasons.append("MTF Alignment: Weekly Trend is Bullish (Tailwind)")
        else:
            score -= 1
            reasons.append("MTF Conflict: Weekly Trend is Bearish (Headwind)")
    else:
        if close.iloc[-1] < current_kama_f:
            score -= 2
            reasons.append("Price below Fast KAMA + Daily Bearish cross")
        else:
            score -= 1
            reasons.append("Daily Bearish cross, but price testing resistance")
            
        if not weekly_trend_up:
            score -= 2
            reasons.append("MTF Alignment: Weekly Trend is Bearish (Tailwind)")
        else:
            score += 1
            reasons.append("MTF Conflict: Weekly Trend is Bullish (Headwind)")
            
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
    
    # Calculate RSI and RVOL for metrics
    rsi_ind = ta.momentum.RSIIndicator(df["Close"], window=14)
    rsi = rsi_ind.rsi().iloc[-1]
    
    # RVOL (Volume / 20-day average)
    avg_vol = df["Volume"].rolling(20).mean().iloc[-1]
    rvol = df["Volume"].iloc[-1] / (avg_vol + 1e-8)
        
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
            "atr": safe_float(atr),
            "rsi": safe_float(rsi),
            "rvol": safe_float(rvol)
        },
        "reasons": reasons
    }

from data.stock_fetcher import get_stock_data

def get_technical_analysis(symbol: str, exchange: str = "NS", period: str = "1y", sector_index: str = "^NSEI") -> Optional[Dict[str, Any]]:
    """Backward compatibility wrapper for API."""
    from data.data_validator import DataQualityError
    
    try:
        df = get_stock_data(symbol, period=period, exchange=exchange)
        if not df or len(df) == 0:
            return None
    except DataQualityError as e:
        import database as db
        try:
            from .regime import get_smoothed_market_regime
            current_regime_name = get_smoothed_market_regime().get("regime", "unknown")
        except:
            current_regime_name = "unknown"
            
        try:
            db.log_signal({
                "symbol": symbol,
                "signal": "VETOED",
                "regime": current_regime_name,
                "score": 0,
                "reasons": [f"Data validation failed: {str(e)}"]
            })
        except Exception as dbe:
            print(f"Failed to log signal to DB: {dbe}")
            
        try:
            db.log_veto({
                "symbol": symbol,
                "type": "DATA_QUALITY",
                "severity": "HIGH",
                "reason": str(e)
            })
        except Exception as dbe:
            print(f"Failed to log veto to DB: {dbe}")
            
        print(f"Skipping {symbol} due to DataQualityError: {e}")
        return None
        
        
    signal_data = calculate_technical_signal(pd.DataFrame(df))
    close_price = df[-1]["Close"] if isinstance(df, list) and len(df) > 0 else 0
    atr = signal_data["metrics"].get("atr", close_price * 0.02)
    from .regime import get_smoothed_market_regime
    from .ensemble import get_ensemble_analysis
    
    # Get Market Regime (Module 2)
    regime_data = get_smoothed_market_regime()
    current_regime_name = regime_data.get("regime", "low_vol_chop")
    vix = regime_data.get("vix_level", 15)
    
    # Upgrade 2: Regime-Adaptive Stop Loss & Upgrade 7: Conservative Targets
    if current_regime_name == "low_vol_uptrend":
        atr_multiplier = 2.0
        cons_target_pct = 1.0
        max_risk_cap = 1.5
    elif current_regime_name == "high_vol_uptrend":
        atr_multiplier = 1.3
        cons_target_pct = 0.6
        max_risk_cap = 0.5
    elif current_regime_name == "low_vol_chop":
        atr_multiplier = 1.5
        cons_target_pct = 0.7
        max_risk_cap = 0.75
    elif current_regime_name == "crisis":
        atr_multiplier = 0.8
        cons_target_pct = 0.4
        max_risk_cap = 0.25
    else:
        atr_multiplier = 1.0
        cons_target_pct = 0.5
        max_risk_cap = 0.5
        
    # Proper Risk/Reward calculation (2.5 minimum per Antigravity v2.0)
    # NOTE: We compute stop/target AFTER the ensemble so the final signal
    # determines the direction. This fixes Bug 1 where SHORT trades had
    # LONG-style stop/target because the raw technical signal was used.
    
    # Run 8-Model Ensemble FIRST (Module 3) — we need the final signal
    ensemble_result = get_ensemble_analysis(symbol, pd.DataFrame(df), current_regime_name)
    
    # Override signal and score with actual Ensemble
    final_signal = ensemble_result["signal"]
    base_score = ensemble_result["confidence"]
    
    # Fix 3: VIX data integrity failure
    if vix == 0 or vix is None:
        final_signal = "VETOED"
        if "reasons" not in signal_data:
            signal_data["reasons"] = []
        signal_data["reasons"].insert(0, "⚠️ VETOED: VIX Data Feed Error. Trading blind is disabled.")
        
    # Task 5: Delivery Volume Filter (only applies to BUY signals — irrelevant for shorts)
    from data.stock_fetcher import _get_delivery_percentage
    delivery_pct = _get_delivery_percentage(symbol)
    if delivery_pct > 0 and delivery_pct < 40.0 and final_signal in ["BUY", "STRONG_BUY"]:
        final_signal = "VETOED"
        if "reasons" not in signal_data:
            signal_data["reasons"] = []
        signal_data["reasons"].insert(0, f"⚠️ VETOED: Low Institutional Delivery ({delivery_pct:.1f}% < 40%).")
    
    # ─── BUG 1 FIX: Compute stop/target using FINAL signal ───
    if final_signal in ["SELL", "STRONG_SELL"]:
        stop_loss = close_price + (atr * atr_multiplier)
        target = close_price - (atr * atr_multiplier * 2.5)
        conservative_target = close_price - ((close_price - target) * cons_target_pct)
    elif final_signal in ["BUY", "STRONG_BUY"]:
        stop_loss = close_price - (atr * atr_multiplier)
        target = close_price + (atr * atr_multiplier * 2.5)
        conservative_target = close_price + ((target - close_price) * cons_target_pct)
    else:
        stop_loss = close_price - (atr * atr_multiplier)
        target = close_price + (atr * atr_multiplier * 1.5)
        conservative_target = close_price + ((target - close_price) * cons_target_pct)

    reward_pct = round(abs((target - close_price) / close_price) * 100, 2)
    risk_pct = round(abs((close_price - stop_loss) / close_price) * 100, 2)
    rr_ratio = round(reward_pct / risk_pct, 2) if risk_pct > 0 else 0
    
    # Upgrade 4: Regime-Adjusted Position Sizing
    win_prob = base_score / 100.0
    kelly_pct = 0
    if rr_ratio > 0:
        kelly_pct = win_prob - ((1.0 - win_prob) / rr_ratio)
        
    quarter_kelly = max(0.0, (kelly_pct / 4.0) * 100)
    suggested_allocation_pct = min(max_risk_cap, quarter_kelly) if final_signal in ["BUY", "SELL"] else 0.0

    # Assemble Score Breakdown mapping for the UI
    votes = ensemble_result["votes"]
    score_breakdown = {
        "Transformer AI": int(votes.get("transformer", 0) * 100) if votes.get("transformer", 0) > 0 else 40,
        "Technical": int(votes.get("technicals", 0) * 100) if votes.get("technicals", 0) > 0 else 40,
        "Momentum": int(votes.get("momentum", 0) * 100) if votes.get("momentum", 0) > 0 else 40,
        "Mean Reversion": int(votes.get("mean_reversion", 0) * 100) if votes.get("mean_reversion", 0) > 0 else 40,
        "Inst. Options": 70 if votes.get("options_flow", 0) > 0 else (30 if votes.get("options_flow", 0) < 0 else 50),
        "Fundamentals": 50 # Placeholder
    }
    
    # Generate reasons including the Macro/Regime veto context
    reasons = signal_data.get("reasons", [])
    if final_signal == "VETOED" and ensemble_result.get("veto_source", "N/A") != "N/A":
        reasons.insert(0, f"⚠️ VETOED by {ensemble_result['veto_source']} filter (Regime: {current_regime_name})")
    elif ensemble_result["macro_status"] == "MACRO TAILWIND":
        reasons.insert(0, "✅ Macro Tailwind active: Reduced confidence threshold applied.")
    
    # ─── Accuracy: RSI Extreme Zone Penalty ───────────────────
    rsi_val = signal_data.get("metrics", {}).get("rsi", 50)
    if final_signal in ["BUY", "STRONG_BUY"] and rsi_val > 75:
        base_score = max(0, base_score - 15)
        reasons.insert(0, f"⚠️ RSI Overbought ({rsi_val:.1f} > 75): Score penalised.")
    elif final_signal in ["SELL", "STRONG_SELL"] and rsi_val < 25:
        base_score = max(0, base_score - 15)
        reasons.insert(0, f"⚠️ RSI Oversold ({rsi_val:.1f} < 25): Score penalised.")
    
    # ─── BUG 2 FIX: RSI gate for SHORT signals ───────────────
    if final_signal in ["SELL", "STRONG_SELL"] and rsi_val < 35:
        final_signal = "VETOED"
        reasons.insert(0, f"⚠️ VETOED: RSI too low for SHORT ({rsi_val:.0f} < 35). Reversal bounce risk.")
    
    # ─── Accuracy: RVOL Conviction Gate ───────────────────────
    rvol_val = signal_data.get("metrics", {}).get("rvol", 1.0)
    if final_signal in ["BUY", "STRONG_BUY"] and rvol_val < 0.5:
        final_signal = "VETOED"
        reasons.insert(0, f"⚠️ VETOED: RVOL too low ({rvol_val:.2f}x < 0.5x). No volume conviction.")
    
    # ─── BUG 4 FIX: RVOL gate for SHORT signals ──────────────
    if final_signal in ["SELL", "STRONG_SELL"] and rvol_val < 0.7:
        final_signal = "VETOED"
        reasons.insert(0, f"⚠️ VETOED: RVOL too low for SHORT ({rvol_val:.2f}x < 0.7x). Need some selling volume.")
    
    # ─── Stale Data Protection ────────────────────────────────
    try:
        from datetime import datetime, timedelta
        last_date_str = df[-1]["Date"] if isinstance(df, list) else str(df.iloc[-1].get("Date", ""))
        last_date = pd.to_datetime(last_date_str)
        now = pd.Timestamp.now()
        stale_threshold = 4 if now.weekday() in [0, 1] else 2
        if (now - last_date).days > stale_threshold:
            final_signal = "VETOED"
            reasons.insert(0, f"⚠️ VETOED: Data is stale ({last_date_str}).")
    except Exception:
        pass
    
    # ─── Save Prediction for Next-Day Grading ─────────────────
    try:
        import database as db_mod
        from datetime import datetime, timedelta
        pred_atr = signal_data["metrics"].get("atr", close_price * 0.02)
        pred_high = close_price + pred_atr
        pred_low = close_price - pred_atr
        pred_support = close_price - (pred_atr * 1.5)
        pred_resistance = close_price + (pred_atr * 1.5)
        if final_signal in ["BUY", "STRONG_BUY"]:
            pred_direction = "Bullish"
        elif final_signal in ["SELL", "STRONG_SELL"]:
            pred_direction = "Bearish"
        else:
            pred_direction = "Neutral"
        today = datetime.now()
        if today.weekday() == 4:
            target_date = today + timedelta(days=3)
        elif today.weekday() == 5:
            target_date = today + timedelta(days=2)
        else:
            target_date = today + timedelta(days=1)
        db_mod.save_intraday_prediction(
            symbol=symbol, pred_high=round(pred_high, 2), pred_low=round(pred_low, 2),
            pred_support=round(pred_support, 2), pred_resistance=round(pred_resistance, 2),
            pred_direction=pred_direction, target_date=target_date.strftime("%Y-%m-%d")
        )
    except Exception as pred_err:
        print(f"Non-fatal: Prediction save failed for {symbol}: {pred_err}")

    # ─── VALIDATION GATE: Hard block invalid SHORT setups ─────
    if final_signal in ["SELL", "STRONG_SELL"]:
        if target >= close_price or stop_loss <= close_price:
            stop_loss = close_price + (atr * atr_multiplier)
            target = close_price - (atr * atr_multiplier * 2.5)
            conservative_target = close_price - ((close_price - target) * cons_target_pct)
            reward_pct = round(abs((target - close_price) / close_price) * 100, 2)
            risk_pct = round(abs((close_price - stop_loss) / close_price) * 100, 2)
            rr_ratio = round(reward_pct / risk_pct, 2) if risk_pct > 0 else 0

    return {
        "symbol": symbol,
        "signal": final_signal,
        "signal_label": ensemble_result.get("signal_label", final_signal),
        "score": base_score,
        "score_breakdown": score_breakdown,
        "reasons": reasons,
        "entry": close_price,
        "target": target,
        "conservative_target": conservative_target,
        "stop_loss": stop_loss,
        "risk_reward": f"1:{rr_ratio:.2f}",
        "reward_pct": reward_pct,
        "risk_pct": risk_pct,
        "allocation_pct": round(suggested_allocation_pct, 2),
        "regime_cap_applied": max_risk_cap,
        "holding_period": "3-5 Days",
        "metrics": signal_data.get("metrics", {}),
        "delivery_pct": round(delivery_pct, 2),
        "patterns": ensemble_result.get("pattern", {"pattern_name": "None", "confidence": 0, "direction": "neutral"})
    }

def screen_stocks(symbols: list, top_n: int = 10, sector_yahoo_index: str = "^NSEI", direction: str = "LONG") -> list:
    """Screen a list of symbols and return the top N by technical score (parallelized)."""
    import concurrent.futures
    results = []
    
    def process_symbol(symbol):
        try:
            ta_res = get_technical_analysis(symbol, sector_index=sector_yahoo_index)
            if ta_res:
                # UX Transparency Upgrade: Allow NEUTRAL signals through to the UI so the user 
                # can see *why* the top stocks in a sector aren't actionable. 
                # (Note: The Arena Engine still strictly filters for BUY/STRONG_BUY internally).
                if direction == "LONG" and ta_res["signal"] not in ["SELL", "STRONG_SELL"]:
                    return ta_res
                elif direction == "SHORT" and ta_res["signal"] not in ["BUY", "STRONG_BUY"]:
                    return ta_res
        except Exception as e:
            print(f"Error screening {symbol}: {e}")
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_symbol, symbol): symbol for symbol in symbols}
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                results.append(res)
                
    # BUG 5 FIX: Always sort descending — highest score = rank 1 for both longs and shorts
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_n]

