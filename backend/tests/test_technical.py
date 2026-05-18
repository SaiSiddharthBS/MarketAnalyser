"""
Task 11: Unit Tests for Technical Analysis (screen_stocks)
Tests directional filtering and sorting logic.
"""
import pytest
from unittest.mock import patch, MagicMock


def _mock_ta_results():
    """Return a set of mock technical analysis results with varied signals and scores."""
    return {
        "RELIANCE": {"symbol": "RELIANCE", "signal": "BUY", "score": 85},
        "TCS": {"symbol": "TCS", "signal": "SELL", "score": 20},
        "INFY": {"symbol": "INFY", "signal": "BUY", "score": 72},
        "HDFCBANK": {"symbol": "HDFCBANK", "signal": "NEUTRAL", "score": 50},
        "ICICIBANK": {"symbol": "ICICIBANK", "signal": "SELL", "score": 15},
        "SBIN": {"symbol": "SBIN", "signal": "STRONG_BUY", "score": 92},
    }


def _ta_side_effect(symbol, sector_index=None):
    """Side effect function for mocking get_technical_analysis."""
    results = _mock_ta_results()
    return results.get(symbol)


# ─── Direction Filtering ─────────────────────────────────────


@patch('analysis.technical.get_technical_analysis', side_effect=_ta_side_effect)
def test_long_direction_only_returns_buy_signals(mock_ta):
    """LONG direction should only include BUY and STRONG_BUY signals."""
    from analysis.technical import screen_stocks
    symbols = list(_mock_ta_results().keys())
    results = screen_stocks(symbols, top_n=10, direction="LONG")
    for r in results:
        assert r["signal"] in ["BUY", "STRONG_BUY"], \
            f"Got unexpected signal {r['signal']} for {r['symbol']}"
    # Should have RELIANCE (BUY), INFY (BUY), SBIN (STRONG_BUY) = 3
    assert len(results) == 3


@patch('analysis.technical.get_technical_analysis', side_effect=_ta_side_effect)
def test_short_direction_only_returns_sell_signals(mock_ta):
    """SHORT direction should only include SELL and STRONG_SELL signals."""
    from analysis.technical import screen_stocks
    symbols = list(_mock_ta_results().keys())
    results = screen_stocks(symbols, top_n=10, direction="SHORT")
    for r in results:
        assert r["signal"] in ["SELL", "STRONG_SELL"], \
            f"Got unexpected signal {r['signal']} for {r['symbol']}"
    # Should have TCS (SELL), ICICIBANK (SELL) = 2
    assert len(results) == 2


# ─── Sorting ─────────────────────────────────────────────────


@patch('analysis.technical.get_technical_analysis', side_effect=_ta_side_effect)
def test_long_results_sorted_descending_by_score(mock_ta):
    """LONG results should be sorted highest score first."""
    from analysis.technical import screen_stocks
    symbols = list(_mock_ta_results().keys())
    results = screen_stocks(symbols, top_n=10, direction="LONG")
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True), \
        f"Scores not sorted descending: {scores}"


@patch('analysis.technical.get_technical_analysis', side_effect=_ta_side_effect)
def test_short_results_sorted_descending_by_score(mock_ta):
    """SHORT results should be sorted highest score first, as score = confidence."""
    from analysis.technical import screen_stocks
    symbols = list(_mock_ta_results().keys())
    results = screen_stocks(symbols, top_n=10, direction="SHORT")
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True), \
        f"Scores not sorted descending: {scores}"


# ─── top_n Limit ─────────────────────────────────────────────


@patch('analysis.technical.get_technical_analysis', side_effect=_ta_side_effect)
def test_top_n_limits_results(mock_ta):
    """top_n=2 should return at most 2 results."""
    from analysis.technical import screen_stocks
    symbols = list(_mock_ta_results().keys())
    results = screen_stocks(symbols, top_n=2, direction="LONG")
    assert len(results) <= 2
