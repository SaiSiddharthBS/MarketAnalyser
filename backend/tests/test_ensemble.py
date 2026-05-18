"""
Task 11: Unit Tests for Ensemble Voter
Tests confidence capping per regime and signal classification.
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock


def _make_voter():
    """Create a fresh EnsembleVoter with default weights, skipping DB weights."""
    from analysis.ensemble import EnsembleVoter
    with patch.object(EnsembleVoter, '_load_regime_weights', return_value={
        "options_flow": 25,
        "transformer": 22,
        "regime": 18,
        "technicals": 15,
        "momentum": 10,
        "mean_reversion": 6,
        "fundamentals": 3,
        "sentiment": 1
    }):
        voter = EnsembleVoter()
    return voter


def _all_bullish_votes(voter):
    """Return votes where every model votes +1."""
    return {model: 1 for model in voter.weights.keys()}


def _all_bearish_votes(voter):
    """Return votes where every model votes -1."""
    return {model: -1 for model in voter.weights.keys()}


def _safe_metrics(rvol=2.0, rsi=50):
    """Return metrics that won't trigger RVOL penalty or RSI veto."""
    return {"rvol": rvol, "rsi": rsi}


def _neutral_pattern():
    return {"pattern_name": "None", "confidence": 0, "direction": "neutral"}


def _clear_macro():
    return {"status": "CLEAR"}


# ─── Confidence Capping Tests ────────────────────────────────


@patch('analysis.ensemble.get_macro_environment', return_value=_clear_macro())
@patch('analysis.patterns.detect_patterns', return_value=_neutral_pattern())
def test_crisis_regime_caps_confidence_at_60(mock_pat, mock_macro):
    """In crisis regime, confidence must never exceed 60.0%."""
    voter = _make_voter()
    voter.collect_votes = MagicMock(
        return_value=(_all_bullish_votes(voter), _safe_metrics())
    )
    result = voter.calculate_confidence("TEST", pd.DataFrame(), "crisis")
    assert result["confidence"] <= 60.0
    assert result["confidence_cap"] == 60.0


@patch('analysis.ensemble.get_macro_environment', return_value=_clear_macro())
@patch('analysis.patterns.detect_patterns', return_value=_neutral_pattern())
def test_low_vol_uptrend_caps_at_90(mock_pat, mock_macro):
    """In low_vol_uptrend regime, confidence cap is 90.0%."""
    voter = _make_voter()
    voter.collect_votes = MagicMock(
        return_value=(_all_bullish_votes(voter), _safe_metrics())
    )
    result = voter.calculate_confidence("TEST", pd.DataFrame(), "low_vol_uptrend")
    assert result["confidence"] <= 90.0
    assert result["confidence_cap"] == 90.0


@patch('analysis.ensemble.get_macro_environment', return_value=_clear_macro())
@patch('analysis.patterns.detect_patterns', return_value=_neutral_pattern())
def test_high_vol_uptrend_caps_at_75(mock_pat, mock_macro):
    """In high_vol_uptrend regime, confidence cap is 75.0%."""
    voter = _make_voter()
    voter.collect_votes = MagicMock(
        return_value=(_all_bullish_votes(voter), _safe_metrics())
    )
    result = voter.calculate_confidence("TEST", pd.DataFrame(), "high_vol_uptrend")
    assert result["confidence"] <= 75.0
    assert result["confidence_cap"] == 75.0


@patch('analysis.ensemble.get_macro_environment', return_value=_clear_macro())
@patch('analysis.patterns.detect_patterns', return_value=_neutral_pattern())
def test_low_vol_chop_caps_at_65(mock_pat, mock_macro):
    """In low_vol_chop regime, confidence cap is 65.0%."""
    voter = _make_voter()
    voter.collect_votes = MagicMock(
        return_value=(_all_bullish_votes(voter), _safe_metrics())
    )
    result = voter.calculate_confidence("TEST", pd.DataFrame(), "low_vol_chop")
    assert result["confidence"] <= 65.0
    assert result["confidence_cap"] == 65.0


@patch('analysis.ensemble.get_macro_environment', return_value=_clear_macro())
@patch('analysis.patterns.detect_patterns', return_value=_neutral_pattern())
def test_default_regime_caps_at_60(mock_pat, mock_macro):
    """Unknown/default regime caps at 60.0%."""
    voter = _make_voter()
    voter.collect_votes = MagicMock(
        return_value=(_all_bullish_votes(voter), _safe_metrics())
    )
    result = voter.calculate_confidence("TEST", pd.DataFrame(), "some_other_regime")
    assert result["confidence"] <= 60.0
    assert result["confidence_cap"] == 60.0


# ─── Signal Classification Tests ─────────────────────────────


@patch('analysis.ensemble.get_macro_environment', return_value=_clear_macro())
@patch('analysis.patterns.detect_patterns', return_value=_neutral_pattern())
def test_all_bearish_votes_produce_sell_signal(mock_pat, mock_macro):
    """When every model votes -1, signal should be SELL."""
    voter = _make_voter()
    voter.collect_votes = MagicMock(
        return_value=(_all_bearish_votes(voter), _safe_metrics())
    )
    # Use low_vol_uptrend (sell_threshold = 20). Confidence = 0.0 <= 20 → SELL
    result = voter.calculate_confidence("TEST", pd.DataFrame(), "low_vol_uptrend")
    assert result["signal"] == "SELL"


@patch('analysis.ensemble.get_macro_environment', return_value=_clear_macro())
@patch('analysis.patterns.detect_patterns', return_value=_neutral_pattern())
def test_rvol_veto_prevents_buy(mock_pat, mock_macro):
    """A BUY signal should be VETOED if RVOL is below the regime minimum."""
    voter = _make_voter()
    # All bullish votes but RVOL = 0.5 (below every regime minimum)
    voter.collect_votes = MagicMock(
        return_value=(_all_bullish_votes(voter), _safe_metrics(rvol=0.5))
    )
    result = voter.calculate_confidence("TEST", pd.DataFrame(), "low_vol_uptrend")
    assert result["signal"] == "VETOED"
    assert "RVOL" in result["veto_source"]
