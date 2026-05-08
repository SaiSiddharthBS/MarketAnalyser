"""
Agent Alpha v2.0 — Volume Profile & Market Microstructure Model (Model 6)
==========================================================================
Weight in ensemble: 10%

Combines:
- VWAP (Volume Weighted Average Price) — institutional fair value
- Point of Control (POC) — price level with highest traded volume
- Delivery Percentage — conviction scoring (India-specific)
- Relative Volume (RVOL) — institutional activity detector
- Unusual Volume Detection — accumulation/distribution spotter

Price above VWAP = institutional buying zone
Price below VWAP = institutional selling pressure
RVOL > 1.5 + price up = accumulation
RVOL > 1.5 + price down = distribution (strong SELL)
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional


def calculate_vwap(df: pd.DataFrame, period: int = 20) -> Optional[pd.Series]:
    """
    Calculate Volume Weighted Average Price.

    VWAP = Σ(Typical Price × Volume) / Σ(Volume)
    Typical Price = (High + Low + Close) / 3

    Args:
        df: OHLCV DataFrame
        period: Rolling window for VWAP (default 20 days)

    Returns:
        Series of VWAP values
    """
    if df is None or df.empty or len(df) < period:
        return None

    typical_price = (df["High"] + df["Low"] + df["Close"]) / 3
    tp_vol = typical_price * df["Volume"]

    vwap = tp_vol.rolling(window=period).sum() / df["Volume"].rolling(window=period).sum()

    return vwap


def calculate_point_of_control(
    df: pd.DataFrame,
    period: int = 20,
    n_bins: int = 50,
) -> Optional[float]:
    """
    Calculate the Point of Control (POC) — the price level with the
    highest traded volume over the past N days.

    POC acts as a magnet:
    - Price approaching POC from below = resistance
    - Price bouncing off POC = support confirmed

    Args:
        df: OHLCV DataFrame
        period: Lookback period (default 20 days)
        n_bins: Number of price bins for volume profile

    Returns:
        POC price level (float)
    """
    if df is None or df.empty or len(df) < period:
        return None

    recent = df.iloc[-period:]

    price_min = recent["Low"].min()
    price_max = recent["High"].max()

    if price_max <= price_min:
        return float(recent["Close"].iloc[-1])

    # Create price bins
    bins = np.linspace(price_min, price_max, n_bins + 1)
    bin_centers = (bins[:-1] + bins[1:]) / 2
    volume_profile = np.zeros(n_bins)

    # Distribute volume across price bins for each day
    for _, row in recent.iterrows():
        day_low = row["Low"]
        day_high = row["High"]
        day_vol = row["Volume"]

        if day_high <= day_low or day_vol <= 0:
            continue

        # Distribute volume uniformly across the day's range
        for j in range(n_bins):
            bin_low = bins[j]
            bin_high = bins[j + 1]

            # Calculate overlap between day's range and this bin
            overlap_low = max(day_low, bin_low)
            overlap_high = min(day_high, bin_high)

            if overlap_high > overlap_low:
                overlap_pct = (overlap_high - overlap_low) / (day_high - day_low)
                volume_profile[j] += day_vol * overlap_pct

    # POC = bin center with highest volume
    poc_idx = np.argmax(volume_profile)
    poc = float(bin_centers[poc_idx])

    return round(poc, 2)


def calculate_rvol(df: pd.DataFrame, period: int = 20) -> Optional[float]:
    """
    Calculate Relative Volume (today's volume vs 20-day average).

    RVOL > 1.5 = abnormal volume activity (institutional)
    RVOL > 3.0 = extremely unusual (flag for review)
    RVOL < 0.5 = low interest / illiquid day

    Returns:
        RVOL ratio (float)
    """
    if df is None or df.empty or len(df) < period + 1:
        return None

    avg_vol = df["Volume"].iloc[-(period + 1):-1].mean()
    if avg_vol <= 0:
        return None

    today_vol = df["Volume"].iloc[-1]
    rvol = today_vol / avg_vol

    return round(float(rvol), 2)


def calculate_volume_profile_signal(
    df: pd.DataFrame,
    delivery_pct: Optional[float] = None,
    delivery_score: int = 0,
) -> Dict[str, Any]:
    """
    Generate the complete Volume Profile signal for the ensemble.

    Combines VWAP, POC, RVOL, and delivery % into a single directional signal.

    Args:
        df: OHLCV DataFrame (minimum 20 rows)
        delivery_pct: Delivery percentage from delivery_fetcher (or None)
        delivery_score: Pre-calculated delivery score (-1, 0, +2)

    Returns:
        Dict with: signal, confidence, direction, vwap, poc, rvol, breakdown
    """
    if df is None or df.empty or len(df) < 20:
        return {"signal": "NEUTRAL", "confidence": 0, "direction": 0}

    close = float(df["Close"].iloc[-1])
    price_change_pct = float((df["Close"].iloc[-1] / df["Close"].iloc[-2] - 1) * 100) if len(df) > 1 else 0

    # ─── Calculate Components ────────────────────────────────
    vwap_series = calculate_vwap(df)
    vwap = float(vwap_series.iloc[-1]) if vwap_series is not None and not vwap_series.isna().iloc[-1] else close

    poc = calculate_point_of_control(df)
    if poc is None:
        poc = close

    rvol = calculate_rvol(df)
    if rvol is None:
        rvol = 1.0

    # ─── Sub-Signals ─────────────────────────────────────────
    score = 0
    reasons = []

    # 1. Price vs VWAP
    vwap_pct = (close - vwap) / vwap * 100 if vwap > 0 else 0
    if vwap_pct > 1.0:
        score += 2
        reasons.append(f"Price {vwap_pct:.1f}% above VWAP (institutional buying zone)")
    elif vwap_pct > 0:
        score += 1
        reasons.append(f"Price {vwap_pct:.1f}% above VWAP")
    elif vwap_pct < -1.0:
        score -= 2
        reasons.append(f"Price {abs(vwap_pct):.1f}% below VWAP (selling pressure)")
    elif vwap_pct < 0:
        score -= 1
        reasons.append(f"Price {abs(vwap_pct):.1f}% below VWAP")

    # 2. Price vs POC
    poc_dist_pct = (close - poc) / poc * 100 if poc > 0 else 0
    if poc_dist_pct > 2.0:
        score += 1
        reasons.append(f"Price broken above POC ({poc:.0f})")
    elif poc_dist_pct < -2.0:
        score -= 1
        reasons.append(f"Price below POC ({poc:.0f}) — potential support break")
    else:
        reasons.append(f"Price near POC ({poc:.0f}) — magnetic zone")

    # 3. RVOL + Directional context
    if rvol > 3.0:
        if price_change_pct > 0.5:
            score += 3
            reasons.append(f"RVOL {rvol:.1f}x with price UP — strong accumulation")
        elif price_change_pct < -0.5:
            score -= 3
            reasons.append(f"RVOL {rvol:.1f}x with price DOWN — strong distribution")
        else:
            reasons.append(f"RVOL {rvol:.1f}x — extremely unusual volume (direction unclear)")
    elif rvol > 1.5:
        if price_change_pct > 0.3:
            score += 2
            reasons.append(f"RVOL {rvol:.1f}x with price UP — institutional buying")
        elif price_change_pct < -0.3:
            score -= 2
            reasons.append(f"RVOL {rvol:.1f}x with price DOWN — institutional selling")
    elif rvol < 0.5:
        score -= 1
        reasons.append(f"RVOL {rvol:.1f}x — low volume, unreliable signals")

    # 4. Delivery Percentage
    score += delivery_score
    if delivery_pct is not None:
        if delivery_score > 0:
            reasons.append(f"High delivery {delivery_pct:.0f}% — conviction buying")
        elif delivery_score < 0:
            reasons.append(f"Low delivery {delivery_pct:.0f}% — speculative activity")

    # ─── Signal Classification ───────────────────────────────
    if score >= 5:
        signal, direction = "BUY", 1
        confidence = min(95, 60 + score * 5)
    elif score >= 3:
        signal, direction = "BUY", 1
        confidence = min(80, 45 + score * 7)
    elif score >= 1:
        signal, direction = "BUY", 1
        confidence = min(60, 30 + score * 10)
    elif score <= -4:
        signal, direction = "SELL", -1
        confidence = min(90, 50 + abs(score) * 7)
    elif score <= -2:
        signal, direction = "SELL", -1
        confidence = min(70, 35 + abs(score) * 10)
    else:
        signal, direction = "NEUTRAL", 0
        confidence = 40

    return {
        "signal": signal,
        "confidence": confidence,
        "direction": direction,
        "composite_score": score,
        "vwap": round(vwap, 2),
        "price_vs_vwap_pct": round(vwap_pct, 2),
        "poc": poc,
        "rvol": rvol,
        "delivery_pct": delivery_pct,
        "delivery_score": delivery_score,
        "reasons": reasons,
    }
