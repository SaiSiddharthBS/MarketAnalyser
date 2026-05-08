"""
Agent Alpha v2.0 — Master Ensemble Engine
==========================================
The brain of Agent Alpha. Combines all 8 independent signal models
into a single, weighted, conviction-scored trading decision.

Architecture:
    8 models → weighted vote → ensemble score → signal classification
                                                      ↓
                                             Hard Veto override
                                                      ↓
                                             Final signal output

Signal Levels:
    ULTRA HIGH CONVICTION BUY  — 5+ models agree, score > 70
    HIGH CONVICTION BUY        — 4+ models agree, score > 55
    MODERATE BUY               — 3+ models agree, score > 40
    NEUTRAL / STAND ASIDE      — < 3 agree or score < 20
    MODERATE SELL              — 3+ models agree SELL, score < -40
    HIGH CONVICTION SELL       — 4+ models agree SELL, score < -55
    ULTRA HIGH CONVICTION SELL — 5+ models agree SELL, score < -70

Any active hard veto → signal forced to STAND ASIDE, no exceptions.
"""
from typing import Dict, Any, List, Optional


# Default ensemble weights (from alpha_config.yaml)
DEFAULT_WEIGHTS = {
    "momentum": 0.20,
    "order_flow": 0.15,
    "options_implied": 0.15,
    "sentiment": 0.10,
    "institutional": 0.15,
    "volume_profile": 0.10,
    "seasonal": 0.05,
    "insider": 0.10,
}


def calculate_ensemble_signal(
    model_outputs: Dict[str, Dict[str, Any]],
    weights: Optional[Dict[str, float]] = None,
    veto_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Combine all model outputs into the final ensemble signal.

    Args:
        model_outputs: Dict mapping model_name → model output dict.
            Each model output must have: signal (BUY/SELL/NEUTRAL),
            confidence (0-100), direction (-1/0/1)
        weights: Optional override for model weights
        veto_result: Output from VetoEngine.check_all_vetoes()

    Returns:
        Complete ensemble signal dict with conviction level, score,
        model votes breakdown, and risk metrics.
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    # ─── Step 1: Extract model signals ───────────────────────
    model_votes = {}
    buy_votes = 0
    sell_votes = 0
    neutral_votes = 0

    for model_name, output in model_outputs.items():
        if not output:
            continue

        signal = output.get("signal", "NEUTRAL")
        confidence = output.get("confidence", 0)
        direction = output.get("direction", 0)
        weight = weights.get(model_name, 0)

        model_votes[model_name] = {
            "signal": signal,
            "confidence": confidence,
            "direction": direction,
            "weight": weight,
            "weighted_contribution": round(confidence * weight * direction, 2),
        }

        if signal == "BUY":
            buy_votes += 1
        elif signal == "SELL":
            sell_votes += 1
        else:
            neutral_votes += 1

    total_models = len(model_votes)
    if total_models == 0:
        return _empty_signal("No model outputs available")

    # ─── Step 2: Calculate Weighted Ensemble Score ───────────
    # Score = Σ(model_confidence × model_weight × model_direction)
    # Range: approximately -100 to +100
    ensemble_score = sum(
        v["weighted_contribution"] for v in model_votes.values()
    )

    # Normalize to ensure the score is on a consistent scale
    total_weight = sum(weights.get(m, 0) for m in model_votes)
    if total_weight > 0:
        normalized_score = ensemble_score / total_weight
    else:
        normalized_score = 0

    # ─── Step 3: Calculate Model Agreement ───────────────────
    agreement_ratio = max(buy_votes, sell_votes) / total_models if total_models > 0 else 0
    dominant_direction = "BUY" if buy_votes > sell_votes else "SELL" if sell_votes > buy_votes else "NEUTRAL"

    # ─── Step 4: Signal Classification ───────────────────────
    signal_info = _classify_signal(
        normalized_score, buy_votes, sell_votes, total_models
    )

    # ─── Step 5: Apply Hard Veto ─────────────────────────────
    vetoed = False
    veto_override = None

    if veto_result and veto_result.get("vetoed", False):
        vetoed = True
        veto_override = veto_result.get("signal_override", "STAND ASIDE")

        # Override signal
        if veto_override == "EXIT ALL POSITIONS":
            signal_info = {
                "signal": "EXIT ALL POSITIONS",
                "conviction": "CRITICAL",
                "kelly_multiplier": 0.0,
                "action": "Liquidate all holdings immediately",
            }
        else:
            signal_info = {
                "signal": "STAND ASIDE",
                "conviction": "VETOED",
                "kelly_multiplier": 0.0,
                "action": "No new positions — hard veto active",
            }

    # ─── Step 6: Confidence Score ────────────────────────────
    # Final confidence combines: ensemble score strength + model agreement
    if not vetoed:
        base_confidence = abs(normalized_score)
        agreement_boost = agreement_ratio * 20
        final_confidence = min(100, int(base_confidence + agreement_boost))
    else:
        final_confidence = 0

    # ─── Assemble Output ─────────────────────────────────────
    return {
        "symbol": _get_symbol_from_outputs(model_outputs),
        "date": _get_date(),
        "signal": signal_info["signal"],
        "conviction": signal_info.get("conviction", ""),
        "ensemble_score": round(normalized_score, 2),
        "raw_ensemble_score": round(ensemble_score, 2),
        "final_confidence": final_confidence,
        "kelly_multiplier": signal_info.get("kelly_multiplier", 0),

        "model_votes": model_votes,
        "vote_summary": {
            "buy_votes": buy_votes,
            "sell_votes": sell_votes,
            "neutral_votes": neutral_votes,
            "total_models": total_models,
            "agreement_ratio": round(agreement_ratio, 2),
            "dominant_direction": dominant_direction,
        },

        "vetoed": vetoed,
        "veto_override": veto_override,
        "active_vetoes": veto_result.get("active_vetoes", []) if veto_result else [],

        "action": signal_info.get("action", ""),
    }


def _classify_signal(
    score: float,
    buy_votes: int,
    sell_votes: int,
    total_models: int,
) -> Dict[str, Any]:
    """Classify the final signal based on score and vote counts."""

    # ─── BUY Signals ─────────────────────────────────────────
    if buy_votes >= 5 and score > 70:
        return {
            "signal": "ULTRA HIGH CONVICTION BUY",
            "conviction": "ULTRA",
            "kelly_multiplier": 1.5,
            "action": "Size up to 1.5× half-Kelly — maximum conviction",
        }
    elif buy_votes >= 4 and score > 55:
        return {
            "signal": "HIGH CONVICTION BUY",
            "conviction": "HIGH",
            "kelly_multiplier": 1.0,
            "action": "Full half-Kelly position size",
        }
    elif buy_votes >= 3 and score > 40:
        return {
            "signal": "MODERATE BUY",
            "conviction": "MODERATE",
            "kelly_multiplier": 0.5,
            "action": "0.5× half-Kelly — partial position",
        }

    # ─── SELL Signals ────────────────────────────────────────
    elif sell_votes >= 5 and score < -70:
        return {
            "signal": "ULTRA HIGH CONVICTION SELL",
            "conviction": "ULTRA",
            "kelly_multiplier": 1.5,
            "action": "Exit or short — maximum conviction sell",
        }
    elif sell_votes >= 4 and score < -55:
        return {
            "signal": "HIGH CONVICTION SELL",
            "conviction": "HIGH",
            "kelly_multiplier": 1.0,
            "action": "Exit positions — high conviction sell",
        }
    elif sell_votes >= 3 and score < -40:
        return {
            "signal": "MODERATE SELL",
            "conviction": "MODERATE",
            "kelly_multiplier": 0.5,
            "action": "Reduce or exit positions",
        }

    # ─── Neutral / Stand Aside ───────────────────────────────
    elif buy_votes <= 1 and sell_votes <= 1:
        return {
            "signal": "STAND ASIDE",
            "conviction": "NONE",
            "kelly_multiplier": 0.0,
            "action": "No clear edge — do not trade",
        }
    else:
        return {
            "signal": "NEUTRAL",
            "conviction": "LOW",
            "kelly_multiplier": 0.0,
            "action": "Mixed signals — no trade recommended",
        }


def _empty_signal(reason: str) -> Dict[str, Any]:
    """Return an empty/default signal when no data is available."""
    return {
        "signal": "NO DATA",
        "conviction": "NONE",
        "ensemble_score": 0,
        "final_confidence": 0,
        "kelly_multiplier": 0,
        "model_votes": {},
        "vote_summary": {"buy_votes": 0, "sell_votes": 0, "total_models": 0},
        "vetoed": False,
        "reason": reason,
    }


def _get_symbol_from_outputs(outputs: Dict) -> str:
    """Extract symbol from any model output."""
    for model_output in outputs.values():
        if model_output and "symbol" in model_output:
            return model_output["symbol"]
    return "UNKNOWN"


def _get_date() -> str:
    """Get today's date string."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d")


def update_ensemble_weights(
    current_weights: Dict[str, float],
    decay_report: Dict[str, Any],
) -> Dict[str, float]:
    """
    Dynamically adjust ensemble weights based on alpha decay data.

    If a model's accuracy has decayed:
    - < 8% drop: reduce weight proportionally
    - > 15% drop: suspend model (weight = 0)

    After adjustment, re-normalize weights to sum to 1.0.

    Args:
        current_weights: Current model weights
        decay_report: Output from alpha_decay monitor

    Returns:
        Updated weights dict (normalized to sum to 1.0)
    """
    updated = dict(current_weights)

    for model_name, decay_info in decay_report.items():
        if model_name not in updated:
            continue

        severity = decay_info.get("severity", 0)

        if severity > 0.15:
            # Suspend model entirely
            updated[model_name] = 0
            print(f"⚠️ ENSEMBLE: Model '{model_name}' SUSPENDED (decay: {severity:.1%})")
        elif severity > 0.08:
            # Proportional reduction
            reduction = severity / 0.15
            updated[model_name] *= (1 - reduction)
            print(f"⚠️ ENSEMBLE: Model '{model_name}' weight reduced by {reduction:.0%}")

    # Re-normalize to sum to 1.0
    total = sum(updated.values())
    if total > 0:
        updated = {k: v / total for k, v in updated.items()}

    return updated
