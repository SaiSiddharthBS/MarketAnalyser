"""
Agent Alpha v2.0 — Order Flow Imbalance Model (Model 2)
========================================================
Weight in ensemble: 15%

Order flow measures whether aggressive buyers or sellers are dominant.

Since NSE tick-level data is not freely available, we use the EOD proxy:
    OFI_proxy = (Close - Open) / (High - Low)

This normalized metric tells us:
    +1.0 = buyers dominated all day (opened at low, closed at high)
    -1.0 = sellers dominated all day (opened at high, closed at low)
     0.0 = balanced / indecisive

The cumulative end-of-day OFI direction is a strong predictor
of next-day gap direction.
"""
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any


def calculate_ofi_proxy(df: pd.DataFrame) -> Optional[pd.Series]:
    """
    Calculate the Order Flow Imbalance proxy from OHLCV data.

    Formula: OFI = (Close - Open) / (High - Low)
    Range: [-1, +1]

    Args:
        df: OHLCV DataFrame with Open, High, Low, Close columns

    Returns:
        Series of OFI values, or None if data insufficient
    """
    if df is None or df.empty or len(df) < 5:
        return None

    hl_range = df["High"] - df["Low"]
    # Avoid division by zero (days with no range = doji)
    hl_range = hl_range.replace(0, np.nan)

    ofi = (df["Close"] - df["Open"]) / hl_range
    ofi = ofi.fillna(0)  # Doji days = neutral

    return ofi


def calculate_order_flow_signal(
    df: pd.DataFrame,
    ofi_buy_threshold: float = 0.3,
    ofi_sell_threshold: float = -0.3,
    lookback_cumulative: int = 5,
) -> Dict[str, Any]:
    """
    Generate order flow signal from OHLCV data.

    Signal Logic:
    - OFI > +0.3 = aggressive buying pressure → BUY
    - OFI < -0.3 = aggressive selling pressure → SELL
    - Cumulative OFI over last 5 days gives trend direction
    - Volume-weighted OFI gives conviction-adjusted signal

    Args:
        df: OHLCV DataFrame (minimum 20 rows)
        ofi_buy_threshold: OFI above this = BUY (default 0.3)
        ofi_sell_threshold: OFI below this = SELL (default -0.3)
        lookback_cumulative: Days for cumulative OFI (default 5)

    Returns:
        Dict with: signal, confidence, ofi_today, ofi_cumulative_5d,
                    volume_weighted_ofi, direction
    """
    if df is None or df.empty or len(df) < 10:
        return {
            "signal": "NEUTRAL", "confidence": 0,
            "ofi_today": 0, "direction": 0,
        }

    ofi = calculate_ofi_proxy(df)
    if ofi is None:
        return {
            "signal": "NEUTRAL", "confidence": 0,
            "ofi_today": 0, "direction": 0,
        }

    # Today's OFI
    ofi_today = float(ofi.iloc[-1])

    # Cumulative OFI (last N days)
    ofi_cumulative = float(ofi.iloc[-lookback_cumulative:].sum()) if len(ofi) >= lookback_cumulative else float(ofi.sum())

    # Volume-weighted OFI (higher volume days get more weight)
    vol = df["Volume"].iloc[-lookback_cumulative:]
    ofi_recent = ofi.iloc[-lookback_cumulative:]
    if vol.sum() > 0:
        vw_ofi = float((ofi_recent * vol).sum() / vol.sum())
    else:
        vw_ofi = float(ofi_recent.mean())

    # OFI acceleration (is flow intensifying?)
    if len(ofi) >= 10:
        recent_avg = float(ofi.iloc[-3:].mean())
        older_avg = float(ofi.iloc[-10:-3].mean())
        acceleration = recent_avg - older_avg
    else:
        acceleration = 0.0

    # ─── Signal Generation ───────────────────────────────────
    if ofi_today > ofi_buy_threshold and ofi_cumulative > 0:
        signal = "BUY"
        direction = 1
        # Confidence: higher OFI + positive cumulative = higher confidence
        confidence = min(100, int(abs(ofi_today) * 60 + abs(ofi_cumulative) * 8))
    elif ofi_today < ofi_sell_threshold and ofi_cumulative < 0:
        signal = "SELL"
        direction = -1
        confidence = min(100, int(abs(ofi_today) * 60 + abs(ofi_cumulative) * 8))
    elif ofi_cumulative > 1.5:
        signal = "BUY"
        direction = 1
        confidence = min(80, int(abs(ofi_cumulative) * 15))
    elif ofi_cumulative < -1.5:
        signal = "SELL"
        direction = -1
        confidence = min(80, int(abs(ofi_cumulative) * 15))
    else:
        signal = "NEUTRAL"
        direction = 0
        confidence = max(0, 50 - int(abs(ofi_cumulative) * 20))

    # Boost confidence if acceleration confirms direction
    if (direction > 0 and acceleration > 0.1) or (direction < 0 and acceleration < -0.1):
        confidence = min(100, confidence + 10)

    return {
        "signal": signal,
        "confidence": confidence,
        "direction": direction,
        "ofi_today": round(ofi_today, 4),
        "ofi_cumulative_5d": round(ofi_cumulative, 4),
        "volume_weighted_ofi": round(vw_ofi, 4),
        "ofi_acceleration": round(acceleration, 4),
        "interpretation": _interpret_ofi(ofi_today, ofi_cumulative),
    }


def _interpret_ofi(ofi_today: float, ofi_cumulative: float) -> str:
    """Human-readable interpretation of OFI."""
    if ofi_today > 0.5 and ofi_cumulative > 2:
        return "Strong institutional buying pressure — aggressive accumulation"
    elif ofi_today > 0.3:
        return "Moderate buying pressure — buyers are dominant"
    elif ofi_today < -0.5 and ofi_cumulative < -2:
        return "Strong institutional selling pressure — aggressive distribution"
    elif ofi_today < -0.3:
        return "Moderate selling pressure — sellers are dominant"
    elif abs(ofi_today) < 0.1:
        return "Neutral / indecisive — balanced order flow"
    else:
        return "Mixed order flow — no clear dominant side"
