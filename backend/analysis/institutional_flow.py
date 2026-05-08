"""
Agent Alpha v2.0 — Institutional Flow Model (Model 5)
======================================================
Weight in ensemble: 15%

This model converts raw FII/DII flow data (from fii_dii_fetcher.py)
into a directional trading signal with confidence.

India-Specific Edge:
FII flows are the single most predictive freely-available signal in
Indian equity markets. When FII buys consistently for 5+ days,
the probability of further upside is historically 65-72%.

This model is unique to Indian markets — global quant funds don't
have access to this granularity of institutional flow data.
"""
from typing import Dict, Any, List, Optional


def calculate_institutional_flow_signal(
    flow_signals: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Convert FII/DII flow analysis into a Model 5 ensemble signal.

    Takes the output of fii_dii_fetcher.calculate_fii_dii_signals()
    and produces a standardized signal for the ensemble.

    Args:
        flow_signals: Output from calculate_fii_dii_signals()

    Returns:
        Dict with: signal (BUY/SELL/NEUTRAL), confidence (0-100), direction (-1/0/1)
    """
    if not flow_signals:
        return {"signal": "NEUTRAL", "confidence": 0, "direction": 0}

    total_score = flow_signals.get("total_flow_score", 0)
    consensus = flow_signals.get("institutional_consensus", "unknown")
    fii_consecutive = flow_signals.get("fii_consecutive_days", 0)
    fii_acceleration = flow_signals.get("fii_acceleration", "steady")
    hard_veto = flow_signals.get("hard_veto_active", False)

    # If hard veto is active, override to SELL
    if hard_veto:
        return {
            "signal": "SELL",
            "confidence": 90,
            "direction": -1,
            "reason": flow_signals.get("hard_veto_reason", "FII mass selling"),
            "consensus": consensus,
            "fii_consecutive_days": fii_consecutive,
        }

    # ─── Signal Generation ───────────────────────────────────
    confidence = 0

    if total_score >= 5:
        signal = "BUY"
        direction = 1
        confidence = min(95, 60 + total_score * 5)
    elif total_score >= 3:
        signal = "BUY"
        direction = 1
        confidence = min(80, 45 + total_score * 7)
    elif total_score >= 1:
        signal = "BUY"
        direction = 1
        confidence = min(60, 30 + total_score * 10)
    elif total_score <= -4:
        signal = "SELL"
        direction = -1
        confidence = min(90, 50 + abs(total_score) * 8)
    elif total_score <= -2:
        signal = "SELL"
        direction = -1
        confidence = min(70, 35 + abs(total_score) * 10)
    else:
        signal = "NEUTRAL"
        direction = 0
        confidence = 40

    # ─── Confidence Modifiers ────────────────────────────────

    # Strong consensus boosts confidence
    if consensus == "strong_bullish" and direction >= 0:
        confidence = min(100, confidence + 15)
    elif consensus == "strong_bearish" and direction <= 0:
        confidence = min(100, confidence + 15)
    elif consensus.startswith("divergent"):
        # Divergence reduces confidence by 30%
        confidence = int(confidence * 0.7)

    # Long consecutive streaks boost confidence
    if fii_consecutive >= 10 and direction > 0:
        confidence = min(100, confidence + 10)
    elif fii_consecutive >= 5 and direction > 0:
        confidence = min(100, confidence + 5)

    # Acceleration boosts
    if fii_acceleration == "accelerating" and direction > 0:
        confidence = min(100, confidence + 8)

    return {
        "signal": signal,
        "confidence": confidence,
        "direction": direction,
        "total_flow_score": total_score,
        "consensus": consensus,
        "fii_consecutive_days": fii_consecutive,
        "fii_acceleration": fii_acceleration,
        "rolling_5d_fii_cr": flow_signals.get("rolling_5d_fii_cr", 0),
        "rolling_5d_dii_cr": flow_signals.get("rolling_5d_dii_cr", 0),
    }
