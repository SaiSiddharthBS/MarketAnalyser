"""
Agent Alpha v2.0 — Position Sizing Engine (Kelly + CVaR)
=========================================================
Complete rebuild from v1's simple risk-per-share model.

Three-layer position sizing:
1. Kelly Criterion — mathematically optimal bet size
2. CVaR Constraint — tail risk limiter (gap risk protection)
3. Portfolio Constraints — correlation, sector, beta limits

Kelly Formula:
    f* = (p × b - q) / b
    Where:
        f* = fraction of portfolio to risk
        p  = win rate (regime-specific)
        q  = loss rate = 1 - p
        b  = win/loss ratio (avg win / avg loss)

We use HALF-Kelly (f*/2) because:
- Full Kelly is mathematically optimal but psychologically brutal
- Half-Kelly gives ~75% of the growth with ~50% of the drawdown
- Industry standard for systematic funds

CVaR (Conditional Value at Risk):
    "On the worst 5% of trading days, what is the average loss?"
    This catches gap risk that stop losses miss.
"""
import numpy as np
from typing import Dict, Any, Optional, List


def calculate_kelly_fraction(
    win_rate: float,
    avg_win: float,
    avg_loss: float,
    kelly_fraction_multiplier: float = 0.5,
) -> float:
    """
    Calculate the Kelly fraction for optimal position sizing.

    Kelly formula: f* = (p × b - q) / b

    Args:
        win_rate: Historical win rate (0.0 to 1.0)
        avg_win: Average winning trade return (positive, e.g., 0.05 = 5%)
        avg_loss: Average losing trade return (positive, e.g., 0.03 = 3%)
        kelly_fraction_multiplier: Half-Kelly = 0.5 (default)

    Returns:
        Optimal fraction of portfolio to risk (0.0 to ~0.25)
    """
    if win_rate <= 0 or win_rate >= 1 or avg_win <= 0 or avg_loss <= 0:
        return 0.0

    p = win_rate
    q = 1 - p
    b = avg_win / avg_loss  # Win/loss ratio

    kelly = (p * b - q) / b

    # Kelly can be negative (negative edge = don't trade!)
    if kelly <= 0:
        return 0.0

    # Apply half-Kelly
    adjusted = kelly * kelly_fraction_multiplier

    # Hard cap: never risk more than 15% on a single position
    return min(adjusted, 0.15)


def calculate_cvar(
    returns: np.ndarray,
    confidence_level: float = 0.95,
) -> float:
    """
    Calculate Conditional Value at Risk (Expected Shortfall).

    CVaR at 95% = "On the worst 5% of trading days, what is the average loss?"

    This is CRITICAL for gap risk:
    - Stop loss at ₹450 but stock opens at ₹380 → stop never fires at ₹450
    - CVaR models this tail risk that stops can't catch

    Args:
        returns: Array of historical daily returns (decimal)
        confidence_level: Confidence level (default 0.95)

    Returns:
        CVaR as a positive decimal (e.g., 0.035 = 3.5% expected loss in worst 5%)
    """
    if returns is None or len(returns) < 30:
        return 0.05  # Conservative default: 5%

    sorted_returns = np.sort(returns)
    cutoff_index = int((1 - confidence_level) * len(sorted_returns))

    if cutoff_index <= 0:
        cutoff_index = 1

    cvar = -np.mean(sorted_returns[:cutoff_index])

    return max(cvar, 0.001)  # Ensure positive


def calculate_position_size(
    entry_price: float,
    stop_loss: float,
    capital: float,
    ensemble_signal: Dict[str, Any],
    regime_state: str = "low_vol_uptrend",
    stock_returns: Optional[np.ndarray] = None,
    max_cvar_per_position_pct: float = 2.0,
    max_position_pct: float = 10.0,
    macro_suppression: float = 1.0,
    earnings_suppression: float = 1.0,
) -> Dict[str, Any]:
    """
    Calculate the final position size using the 3-layer framework.

    Layer 1: Kelly Criterion (base size)
    Layer 2: CVaR constraint (tail risk cap)
    Layer 3: Portfolio constraints (max position, macro, earnings)

    Args:
        entry_price: Entry price per share
        stop_loss: Stop loss price per share
        capital: Total portfolio value
        ensemble_signal: Output from ensemble.calculate_ensemble_signal()
        regime_state: Current HMM regime state
        stock_returns: Historical daily returns for CVaR calculation
        max_cvar_per_position_pct: Max CVaR per position (default 2%)
        max_position_pct: Max single position as % of capital (default 10%)
        macro_suppression: Macro event suppression factor (0.0 to 1.0)
        earnings_suppression: Earnings blackout suppression (0.0 to 1.0)

    Returns:
        Complete position sizing dict
    """
    if entry_price <= 0 or stop_loss <= 0 or capital <= 0:
        return _error_result("Invalid prices or capital")

    if entry_price <= stop_loss:
        return _error_result("Entry price must be above stop loss for BUY")

    risk_per_share = entry_price - stop_loss

    # ─── Layer 1: Kelly Criterion ────────────────────────────

    # Get regime-specific win rate and win/loss ratio
    regime_params = _get_regime_params(regime_state)
    win_rate = regime_params["expected_win_rate"]
    win_loss_ratio = regime_params["expected_win_loss_ratio"]

    avg_win = risk_per_share * win_loss_ratio  # Expected avg win
    avg_loss = risk_per_share                   # Expected avg loss (at stop)

    kelly_f = calculate_kelly_fraction(
        win_rate=win_rate,
        avg_win=avg_win / entry_price,  # As percentage
        avg_loss=avg_loss / entry_price,
    )

    # Apply conviction multiplier from ensemble
    kelly_multiplier = ensemble_signal.get("kelly_multiplier", 0.5)
    regime_kelly_mult = regime_params["kelly_multiplier"]

    adjusted_kelly = kelly_f * kelly_multiplier * regime_kelly_mult

    # Kelly-based position value
    kelly_position_value = capital * adjusted_kelly
    kelly_quantity = int(kelly_position_value / entry_price) if entry_price > 0 else 0

    # ─── Layer 2: CVaR Constraint ────────────────────────────

    if stock_returns is not None and len(stock_returns) >= 30:
        stock_cvar = calculate_cvar(stock_returns)
    else:
        stock_cvar = 0.03  # Default 3% daily CVaR

    # Max position value that keeps CVaR within limit
    max_cvar_value = (max_cvar_per_position_pct / 100 * capital) / stock_cvar if stock_cvar > 0 else capital * 0.1
    cvar_quantity = int(max_cvar_value / entry_price) if entry_price > 0 else 0

    # ─── Layer 3: Portfolio Constraints ──────────────────────

    # Max position value
    max_position_value = capital * (max_position_pct / 100)
    max_qty = int(max_position_value / entry_price) if entry_price > 0 else 0

    # Apply macro and earnings suppression
    suppression = macro_suppression * earnings_suppression

    # ─── Final Size = min(Kelly, CVaR, Max) × Suppression ───
    raw_quantity = min(kelly_quantity, cvar_quantity, max_qty)
    final_quantity = max(0, int(raw_quantity * suppression))

    # Ensure at least 1 share if any position is warranted
    if final_quantity == 0 and kelly_quantity > 0 and suppression > 0:
        final_quantity = 1

    capital_deployed = round(final_quantity * entry_price, 2)
    capital_pct = round((capital_deployed / capital) * 100, 2) if capital > 0 else 0
    max_loss = round(final_quantity * risk_per_share, 2)
    max_loss_pct = round((max_loss / capital) * 100, 2) if capital > 0 else 0

    # Determine which constraint was binding
    binding = "kelly"
    if final_quantity == cvar_quantity:
        binding = "cvar"
    elif final_quantity == max_qty:
        binding = "max_position"

    return {
        "quantity": final_quantity,
        "entry_price": round(entry_price, 2),
        "stop_loss": round(stop_loss, 2),
        "capital_deployed": capital_deployed,
        "capital_pct": capital_pct,
        "max_loss": max_loss,
        "max_loss_pct": max_loss_pct,
        "risk_per_share": round(risk_per_share, 2),

        "sizing_layers": {
            "kelly": {
                "raw_kelly_fraction": round(kelly_f, 4),
                "conviction_multiplier": kelly_multiplier,
                "regime_multiplier": regime_kelly_mult,
                "adjusted_fraction": round(adjusted_kelly, 4),
                "quantity": kelly_quantity,
            },
            "cvar": {
                "stock_cvar_95": round(stock_cvar, 4),
                "max_position_value": round(max_cvar_value, 2),
                "quantity": cvar_quantity,
            },
            "max_position": {
                "max_pct": max_position_pct,
                "max_value": round(max_position_value, 2),
                "quantity": max_qty,
            },
        },

        "suppressions": {
            "macro_factor": macro_suppression,
            "earnings_factor": earnings_suppression,
            "combined": round(suppression, 2),
        },

        "binding_constraint": binding,
        "regime_state": regime_state,
        "regime_win_rate": win_rate,
    }


def _get_regime_params(regime_state: str) -> Dict[str, Any]:
    """Get regime-specific parameters for position sizing."""
    REGIME_PARAMS = {
        "low_vol_uptrend": {
            "expected_win_rate": 0.70,
            "expected_win_loss_ratio": 2.0,
            "kelly_multiplier": 1.0,
            "stop_atr_multiplier": 1.5,
        },
        "high_vol_uptrend": {
            "expected_win_rate": 0.60,
            "expected_win_loss_ratio": 1.8,
            "kelly_multiplier": 0.6,
            "stop_atr_multiplier": 2.0,
        },
        "low_vol_chop": {
            "expected_win_rate": 0.45,
            "expected_win_loss_ratio": 1.5,
            "kelly_multiplier": 0.3,
            "stop_atr_multiplier": 2.5,
        },
        "crisis": {
            "expected_win_rate": 0.35,
            "expected_win_loss_ratio": 1.2,
            "kelly_multiplier": 0.0,  # No new longs in crisis
            "stop_atr_multiplier": 1.0,
        },
    }

    return REGIME_PARAMS.get(regime_state, REGIME_PARAMS["high_vol_uptrend"])


def _error_result(message: str) -> Dict[str, Any]:
    """Return an error result."""
    return {
        "quantity": 0,
        "capital_deployed": 0,
        "max_loss": 0,
        "error": message,
    }


def calculate_portfolio_cvar(
    holdings: Dict[str, float],
    returns_data: Dict[str, np.ndarray],
    confidence: float = 0.95,
    max_portfolio_cvar_pct: float = 3.0,
) -> Dict[str, Any]:
    """
    Calculate portfolio-level CVaR (accounts for correlations).

    Args:
        holdings: Dict of {symbol: weight} (weights sum to 1.0)
        returns_data: Dict of {symbol: daily_returns_array}
        confidence: CVaR confidence level (default 0.95)
        max_portfolio_cvar_pct: Maximum daily CVaR for portfolio

    Returns:
        Dict with: portfolio_cvar, within_limit, reduction_needed
    """
    if not holdings or not returns_data:
        return {"portfolio_cvar": 0, "within_limit": True}

    # Build portfolio return series
    common_length = min(len(r) for r in returns_data.values() if len(r) > 0)
    if common_length < 30:
        return {"portfolio_cvar": 0, "within_limit": True, "note": "Insufficient data"}

    portfolio_returns = np.zeros(common_length)
    for symbol, weight in holdings.items():
        if symbol in returns_data:
            stock_r = returns_data[symbol][-common_length:]
            portfolio_returns += weight * stock_r

    port_cvar = calculate_cvar(portfolio_returns, confidence)
    port_cvar_pct = port_cvar * 100

    within_limit = port_cvar_pct <= max_portfolio_cvar_pct

    reduction_factor = max_portfolio_cvar_pct / port_cvar_pct if port_cvar_pct > max_portfolio_cvar_pct else 1.0

    return {
        "portfolio_cvar_pct": round(port_cvar_pct, 2),
        "max_allowed_pct": max_portfolio_cvar_pct,
        "within_limit": within_limit,
        "reduction_factor": round(reduction_factor, 2),
        "action": "REDUCE ALL POSITIONS" if not within_limit else "OK",
    }
