"""
Task 11: Unit Tests for Regime Classifier
Tests the rule-based fallback regime classification logic.
"""
import pytest
import pandas as pd
import numpy as np


def _make_regime_df(vix, dist_ema200, n_rows=6):
    """Build a minimal DataFrame the fallback classifier can consume."""
    return pd.DataFrame({
        "VIX": [vix] * n_rows,
        "Dist_EMA200": [dist_ema200] * n_rows,
        "Return": [0.001] * n_rows,
        "Vol_20d": [0.15] * n_rows,
        "Breadth": [0.02] * n_rows,
    })


def _get_classifier():
    from analysis.regime import RegimeClassifier
    return RegimeClassifier()


# ─── Rule-Based Regime Classification ────────────────────────


def test_crisis_triggered_by_high_vix():
    """VIX >= 25 should classify as crisis regardless of EMA distance."""
    clf = _get_classifier()
    df = _make_regime_df(vix=30.0, dist_ema200=0.05)
    result = clf._fallback_rule_based_regime(df)
    assert result["regime"] == "crisis"


def test_crisis_triggered_by_negative_ema_distance():
    """Price below 200 EMA (negative Dist_EMA200) should classify as crisis."""
    clf = _get_classifier()
    df = _make_regime_df(vix=15.0, dist_ema200=-0.03)
    result = clf._fallback_rule_based_regime(df)
    assert result["regime"] == "crisis"


def test_low_vol_uptrend_classification():
    """VIX < 18 and Dist_EMA200 > 0.02 should be low_vol_uptrend."""
    clf = _get_classifier()
    df = _make_regime_df(vix=14.0, dist_ema200=0.05)
    result = clf._fallback_rule_based_regime(df)
    assert result["regime"] == "low_vol_uptrend"


def test_high_vol_uptrend_classification():
    """VIX >= 18 and Dist_EMA200 > 0 should be high_vol_uptrend."""
    clf = _get_classifier()
    df = _make_regime_df(vix=20.0, dist_ema200=0.01)
    result = clf._fallback_rule_based_regime(df)
    assert result["regime"] == "high_vol_uptrend"


def test_low_vol_chop_classification():
    """VIX < 18 and small positive Dist_EMA200 (<=0.02) should be low_vol_chop."""
    clf = _get_classifier()
    # VIX=15 (< 18), dist_ema200=0.01 (> 0 but <= 0.02)
    # This doesn't match low_vol_uptrend (needs > 0.02) or high_vol_uptrend (needs VIX >= 18)
    # So it falls through to the else → low_vol_chop
    df = _make_regime_df(vix=15.0, dist_ema200=0.01)
    result = clf._fallback_rule_based_regime(df)
    assert result["regime"] == "low_vol_chop"


def test_empty_dataframe_returns_unknown():
    """An empty DataFrame should safely return 'unknown' regime."""
    clf = _get_classifier()
    result = clf._fallback_rule_based_regime(pd.DataFrame())
    assert result["regime"] == "unknown"
    assert result["confidence_pct"] == 0.0


def test_crisis_probability_on_vix_spike():
    """A 20%+ VIX spike over 5 days should set crisis_probability > 0."""
    clf = _get_classifier()
    # VIX spikes from 15 to 20 over the last 5 rows (33% increase > 20%)
    df = pd.DataFrame({
        "VIX": [15.0, 15.0, 16.0, 17.0, 18.0, 20.0],
        "Dist_EMA200": [0.05] * 6,
        "Return": [0.001] * 6,
        "Vol_20d": [0.15] * 6,
        "Breadth": [0.02] * 6,
    })
    result = clf._fallback_rule_based_regime(df)
    assert result["crisis_probability_tomorrow_pct"] == 40.0


def test_regime_output_has_required_fields():
    """Every regime output must contain the standard fields."""
    clf = _get_classifier()
    df = _make_regime_df(vix=14.0, dist_ema200=0.05)
    result = clf._fallback_rule_based_regime(df)
    required_fields = [
        "regime", "status", "color", "emoji",
        "confidence_pct", "crisis_probability_tomorrow_pct",
        "method", "vix_level", "nifty_vs_200ema_pct", "date"
    ]
    for field in required_fields:
        assert field in result, f"Missing field: {field}"
