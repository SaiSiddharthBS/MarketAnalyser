"""
Agent Alpha v2.0 — Portfolio Optimizer (Correlation + Beta Management)
======================================================================
The position sizing engine calculates SIZE per trade.
This module manages the PORTFOLIO as a whole.

Rules:
1. Max correlation between any two positions: 0.65
2. Max 3 stocks from same sector
3. Max 25% in any single sector
4. Portfolio beta within regime-specific target range
5. Greedy selection: highest score + lowest correlation to existing

Why correlation matters:
If you hold HDFCBANK + ICICIBANK + KOTAKBANK, you think you have
3 positions. In reality, you have 1 position (banking sector) with
3× the size. A single RBI announcement moves all three identically.
Correlation management prevents this concentration trap.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple


def calculate_correlation_matrix(
    returns_data: Dict[str, pd.Series],
    lookback: int = 60,
) -> Optional[pd.DataFrame]:
    """
    Calculate pairwise correlation matrix for a set of stocks.

    Args:
        returns_data: Dict mapping symbol → daily returns series
        lookback: Number of days for rolling correlation (default 60)

    Returns:
        DataFrame of pairwise correlations, or None
    """
    if not returns_data or len(returns_data) < 2:
        return None

    # Build a DataFrame of returns
    df = pd.DataFrame()
    for symbol, returns in returns_data.items():
        if returns is not None and len(returns) >= lookback:
            df[symbol] = returns.iloc[-lookback:].values[:lookback]

    if len(df.columns) < 2:
        return None

    return df.corr()


def check_portfolio_correlation(
    existing_positions: List[str],
    candidate_symbol: str,
    returns_data: Dict[str, pd.Series],
    max_correlation: float = 0.65,
) -> Dict[str, Any]:
    """
    Check if adding a new stock would violate correlation constraints.

    Args:
        existing_positions: List of symbols currently held
        candidate_symbol: Symbol we want to add
        returns_data: Dict of daily returns per symbol
        max_correlation: Maximum allowed pairwise correlation

    Returns:
        Dict with: can_add (bool), max_corr_with, corr_value, details
    """
    if not existing_positions:
        return {"can_add": True, "max_corr_with": None, "corr_value": 0}

    if candidate_symbol not in returns_data:
        return {"can_add": True, "note": "No return data for candidate — allowing by default"}

    candidate_returns = returns_data[candidate_symbol]
    if candidate_returns is None or len(candidate_returns) < 30:
        return {"can_add": True, "note": "Insufficient data for correlation check"}

    max_corr = 0.0
    max_corr_symbol = None
    violations = []

    for pos_symbol in existing_positions:
        if pos_symbol not in returns_data:
            continue

        pos_returns = returns_data[pos_symbol]
        if pos_returns is None or len(pos_returns) < 30:
            continue

        # Calculate pairwise correlation
        min_len = min(len(candidate_returns), len(pos_returns))
        corr = float(np.corrcoef(
            candidate_returns.values[-min_len:],
            pos_returns.values[-min_len:]
        )[0, 1])

        if abs(corr) > abs(max_corr):
            max_corr = corr
            max_corr_symbol = pos_symbol

        if abs(corr) > max_correlation:
            violations.append({
                "symbol": pos_symbol,
                "correlation": round(corr, 3),
            })

    can_add = len(violations) == 0

    return {
        "can_add": can_add,
        "max_corr_with": max_corr_symbol,
        "corr_value": round(max_corr, 3),
        "violations": violations,
        "detail": (
            f"Highest correlation: {max_corr:.3f} with {max_corr_symbol}" 
            if max_corr_symbol else "No existing positions to check"
        ),
    }


def check_sector_constraints(
    existing_positions: List[Dict[str, Any]],
    candidate_symbol: str,
    candidate_sector: str,
    candidate_value: float,
    capital: float,
    max_stocks_per_sector: int = 3,
    max_sector_pct: float = 25.0,
) -> Dict[str, Any]:
    """
    Check sector concentration constraints.

    Args:
        existing_positions: List of dicts with 'symbol', 'sector', 'value'
        candidate_symbol: Symbol to add
        candidate_sector: Sector of candidate
        candidate_value: Value of proposed position
        capital: Total portfolio capital
        max_stocks_per_sector: Max stocks per sector (default 3)
        max_sector_pct: Max % per sector (default 25%)

    Returns:
        Dict with: can_add, stocks_in_sector, sector_pct, violations
    """
    sector_stocks = [
        p for p in existing_positions
        if p.get("sector", "") == candidate_sector
    ]
    sector_count = len(sector_stocks)
    sector_value = sum(p.get("value", 0) for p in sector_stocks)

    new_sector_value = sector_value + candidate_value
    new_sector_pct = (new_sector_value / capital * 100) if capital > 0 else 0

    violations = []

    if sector_count >= max_stocks_per_sector:
        violations.append(
            f"Already {sector_count} stocks in {candidate_sector} (max: {max_stocks_per_sector})"
        )

    if new_sector_pct > max_sector_pct:
        violations.append(
            f"Sector {candidate_sector} would be {new_sector_pct:.1f}% of portfolio (max: {max_sector_pct}%)"
        )

    return {
        "can_add": len(violations) == 0,
        "stocks_in_sector": sector_count,
        "current_sector_pct": round(sector_value / capital * 100, 1) if capital > 0 else 0,
        "proposed_sector_pct": round(new_sector_pct, 1),
        "violations": violations,
    }


def calculate_portfolio_beta(
    holdings: Dict[str, float],
    stock_betas: Dict[str, float],
) -> float:
    """
    Calculate weighted portfolio beta.

    Args:
        holdings: Dict of {symbol: weight} (weights should sum to ~1.0)
        stock_betas: Dict of {symbol: beta_vs_nifty}

    Returns:
        Portfolio beta (e.g., 1.1 = 10% more volatile than Nifty)
    """
    if not holdings or not stock_betas:
        return 1.0

    weighted_beta = 0.0
    total_weight = 0.0

    for symbol, weight in holdings.items():
        beta = stock_betas.get(symbol, 1.0)
        weighted_beta += weight * beta
        total_weight += weight

    return round(weighted_beta / total_weight, 2) if total_weight > 0 else 1.0


def optimize_portfolio_selection(
    candidates: List[Dict[str, Any]],
    returns_data: Dict[str, pd.Series],
    existing_positions: List[Dict[str, Any]],
    capital: float,
    max_positions: int = 20,
    max_correlation: float = 0.65,
    max_stocks_per_sector: int = 3,
    max_sector_pct: float = 25.0,
) -> List[Dict[str, Any]]:
    """
    Greedy portfolio optimization: select candidates that maximize
    score while respecting all constraints.

    Algorithm:
    1. Sort candidates by ensemble score (descending)
    2. For each candidate:
       a. Check correlation with existing + already-selected
       b. Check sector constraints
       c. If passes all checks → ADD to portfolio
       d. If fails → SKIP

    Args:
        candidates: List of dicts with 'symbol', 'sector', 'ensemble_score', 'value'
        returns_data: Dict of daily returns per symbol
        existing_positions: Current portfolio positions
        capital: Total capital
        max_positions: Maximum total positions

    Returns:
        Filtered list of candidates that pass all constraints
    """
    # Sort by score descending
    sorted_candidates = sorted(
        candidates,
        key=lambda x: x.get("ensemble_score", 0),
        reverse=True
    )

    selected = []
    selected_symbols = [p.get("symbol") for p in existing_positions]
    current_positions = list(existing_positions)

    for candidate in sorted_candidates:
        if len(selected_symbols) >= max_positions:
            break

        symbol = candidate.get("symbol", "")
        sector = candidate.get("sector", "UNKNOWN")
        value = candidate.get("value", 0)

        if symbol in selected_symbols:
            continue

        # ─── Check Correlation ───────────────────────────────
        corr_check = check_portfolio_correlation(
            selected_symbols, symbol, returns_data, max_correlation
        )
        if not corr_check["can_add"]:
            candidate["rejected_reason"] = f"Correlation too high: {corr_check['detail']}"
            continue

        # ─── Check Sector ────────────────────────────────────
        sector_check = check_sector_constraints(
            current_positions, symbol, sector, value, capital,
            max_stocks_per_sector, max_sector_pct
        )
        if not sector_check["can_add"]:
            candidate["rejected_reason"] = f"Sector constraint: {sector_check['violations']}"
            continue

        # ─── Passed All Checks ───────────────────────────────
        selected.append(candidate)
        selected_symbols.append(symbol)
        current_positions.append({
            "symbol": symbol,
            "sector": sector,
            "value": value,
        })

    return selected
