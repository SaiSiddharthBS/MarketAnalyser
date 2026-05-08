"""
Agent Alpha v2.0 — Momentum Crash Early Warning System
========================================================
The most dangerous risk for a momentum system: the MOMENTUM CRASH.

What is a momentum crash?
    When too many stocks are in a momentum trade (crowded), a small trigger
    causes simultaneous unwinding → cascading selloff → crash.

    Famous examples:
    - August 2007 Quant Quake (Goldman Sachs quant fund lost 30% in a week)
    - March 2020 COVID crash (momentum stocks fell 30% in 3 weeks)
    - January 2021 (GameStop/WSB forced deleveraging of momentum funds)

Detection Metrics:
    1. Crowding: % of universe near 52-week highs > 45%
    2. Volatility compression: 20d vol / 60d vol < 0.5
    3. Momentum-Value spread: when momentum PE >> value PE
    4. Cross-sectional dispersion: when all stocks move together

Risk Action Table:
    0-30:  Normal — full allocation
    30-50: Elevated — reduce momentum positions by 20%
    50-70: High — reduce momentum positions by 50%
    70-100: Critical — SUSPEND momentum signals entirely
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime


def calculate_momentum_crash_risk(
    stock_data: Dict[str, pd.DataFrame],
    sector_data: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Calculate the Momentum Crash Risk Index (0-100).

    Args:
        stock_data: Dict mapping symbol → OHLCV DataFrame
        sector_data: Optional dict mapping symbol → sector name

    Returns:
        Dict with: crash_risk_score, components, action, details
    """
    if not stock_data or len(stock_data) < 10:
        return {"crash_risk_score": 0, "action": "INSUFFICIENT DATA"}

    components = {}

    # ─── 1. Crowding Detection ───────────────────────────────
    # How many stocks are near their 52-week highs?
    near_52w_high = 0
    total_valid = 0

    for symbol, df in stock_data.items():
        if df is None or df.empty or len(df) < 252:
            continue
        total_valid += 1
        
        close = float(df["Close"].iloc[-1])
        high_52w = float(df["High"].iloc[-252:].max())
        
        if high_52w > 0 and close >= high_52w * 0.95:  # Within 5% of 52w high
            near_52w_high += 1

    crowding_pct = (near_52w_high / total_valid * 100) if total_valid > 0 else 0
    
    if crowding_pct > 55:
        crowding_score = 35
    elif crowding_pct > 45:
        crowding_score = 25
    elif crowding_pct > 35:
        crowding_score = 15
    else:
        crowding_score = 5

    components["crowding"] = {
        "pct_near_52w_high": round(crowding_pct, 1),
        "score": crowding_score,
        "threshold": 45,
        "status": "CROWDED" if crowding_pct > 45 else "NORMAL",
    }

    # ─── 2. Volatility Compression ──────────────────────────
    # When short-term vol drops well below long-term vol, it often
    # precedes a volatility expansion (which kills momentum)
    vol_ratios = []

    for symbol, df in stock_data.items():
        if df is None or len(df) < 60:
            continue
        returns = df["Close"].pct_change().dropna()
        if len(returns) < 60:
            continue

        vol_20d = float(returns.iloc[-20:].std())
        vol_60d = float(returns.iloc[-60:].std())

        if vol_60d > 0:
            vol_ratios.append(vol_20d / vol_60d)

    avg_vol_ratio = np.mean(vol_ratios) if vol_ratios else 1.0

    if avg_vol_ratio < 0.4:
        vol_score = 30  # Extreme compression → high risk
    elif avg_vol_ratio < 0.5:
        vol_score = 20
    elif avg_vol_ratio < 0.7:
        vol_score = 10
    else:
        vol_score = 0

    components["vol_compression"] = {
        "avg_vol_ratio": round(avg_vol_ratio, 3),
        "score": vol_score,
        "threshold": 0.5,
        "status": "COMPRESSED" if avg_vol_ratio < 0.5 else "NORMAL",
    }

    # ─── 3. Cross-Sectional Dispersion ──────────────────────
    # When ALL stocks move together (low dispersion), it means
    # macro/sentiment is driving everything → regime is fragile
    daily_returns = []

    for symbol, df in stock_data.items():
        if df is None or len(df) < 5:
            continue
        ret = float((df["Close"].iloc[-1] / df["Close"].iloc[-2] - 1))
        daily_returns.append(ret)

    if daily_returns:
        dispersion = np.std(daily_returns)
        # Historical 10th percentile for Indian markets ≈ 0.005
        if dispersion < 0.005:
            dispersion_score = 20  # Very low → herding behavior
        elif dispersion < 0.008:
            dispersion_score = 10
        else:
            dispersion_score = 0
    else:
        dispersion = 0
        dispersion_score = 0

    components["dispersion"] = {
        "cross_sectional_std": round(dispersion, 5),
        "score": dispersion_score,
        "status": "LOW DISPERSION" if dispersion < 0.005 else "NORMAL",
    }

    # ─── 4. Momentum-Value Spread ────────────────────────────
    # When momentum stocks trade at extreme premiums to value stocks
    momentum_returns = []
    value_returns = []

    for symbol, df in stock_data.items():
        if df is None or len(df) < 60:
            continue
        ret_3m = float(df["Close"].iloc[-1] / df["Close"].iloc[-60] - 1) if len(df) >= 60 else 0

        if ret_3m > 0.15:  # Top momentum: >15% return in 3 months
            momentum_returns.append(ret_3m)
        elif ret_3m < -0.05:  # Value: negative 3-month return
            value_returns.append(ret_3m)

    if momentum_returns and value_returns:
        mv_spread = np.mean(momentum_returns) - np.mean(value_returns)
        if mv_spread > 0.40:  # 40%+ spread = extreme
            mv_score = 15
        elif mv_spread > 0.25:
            mv_score = 8
        else:
            mv_score = 0
    else:
        mv_spread = 0
        mv_score = 0

    components["momentum_value_spread"] = {
        "spread": round(mv_spread, 3) if mv_spread else 0,
        "score": mv_score,
        "status": "EXTREME" if mv_score > 10 else "NORMAL",
    }

    # ─── Composite Crash Risk Score ──────────────────────────
    crash_risk = crowding_score + vol_score + dispersion_score + mv_score
    crash_risk = min(100, crash_risk)

    # ─── Action Table ────────────────────────────────────────
    if crash_risk >= 70:
        action = "SUSPEND"
        action_detail = "SUSPEND all momentum signals — crash risk CRITICAL"
        position_reduction = 1.0  # 100% reduction
    elif crash_risk >= 50:
        action = "REDUCE_50"
        action_detail = "Reduce momentum positions by 50% — crash risk HIGH"
        position_reduction = 0.5
    elif crash_risk >= 30:
        action = "REDUCE_20"
        action_detail = "Reduce momentum positions by 20% — crash risk ELEVATED"
        position_reduction = 0.2
    else:
        action = "NORMAL"
        action_detail = "Normal operations — crash risk within limits"
        position_reduction = 0.0

    return {
        "crash_risk_score": crash_risk,
        "action": action,
        "action_detail": action_detail,
        "position_reduction": position_reduction,
        "momentum_multiplier": 1.0 - position_reduction,
        "components": components,
        "stocks_analyzed": total_valid,
        "date": datetime.now().strftime("%Y-%m-%d"),
    }
