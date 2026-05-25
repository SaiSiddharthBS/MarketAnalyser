"""
Agent Alpha v4.0 - Multi-Timeframe Portfolio Bucketing
======================================================
Splits the overall paper trading capital into distinct buckets to enforce Institutional Risk Parity.
Prevents short-term trades from eating all the capital meant for long-term investments.

Buckets:
1. INTRADAY: 15% capital, max 2 pos, tight stops
2. SHORT_TERM / SWING: 35% capital, max 5 pos, moderate stops
3. POSITIONAL / LONG_TERM: 50% capital, max 8 pos, wide stops
"""
import database as db

BUCKETS = {
    "INTRADAY": {
        "capital_allocation_pct": 0.15,
        "max_positions": 2,
        "base_stop_pct": 0.005,      # 0.5%
        "base_target_pct": 0.01,     # 1%
        "exit_type": "EOD",          # Auto exit at End of Day
        "kelly_multiplier": 0.5      # Half kelly for day trades
    },
    "SWING": {
        "capital_allocation_pct": 0.35,
        "max_positions": 5,
        "base_stop_pct": 0.02,       # 2%
        "base_target_pct": 0.05,     # 5%
        "exit_type": "TRAIL",        # Trail until stopped out or target hit
        "kelly_multiplier": 0.3      # Conservative for swings
    },
    "POSITIONAL": {
        "capital_allocation_pct": 0.50,
        "max_positions": 8,
        "base_stop_pct": 0.05,       # 5%
        "base_target_pct": 0.15,     # 15%
        "exit_type": "TRAIL",        # Trail with wide stops
        "kelly_multiplier": 0.2      # Ultra conservative for long hold
    },
    "ARBITRAGE": {
        "capital_allocation_pct": 0.25, # Draws from unused cash
        "max_positions": 4,          # 4 Pairs
        "base_stop_pct": 0.10,       # High dummy stop (Z-score handles exit)
        "base_target_pct": 0.10,     # High dummy target
        "exit_type": "MEAN_REVERT",  # Exit on Z-score crossover
        "kelly_multiplier": 0.5
    }
}

# Alias mapping for classes from Sprint 1
CLASS_MAPPING = {
    "INTRADAY": "INTRADAY",
    "SHORT_TERM": "SWING",
    "SWING": "SWING",
    "POSITIONAL": "POSITIONAL",
    "LONG_TERM": "POSITIONAL",
    "ARBITRAGE": "ARBITRAGE"
}

def get_bucket_config(holding_class: str) -> dict:
    """Returns the configuration for a specific holding class."""
    bucket_name = CLASS_MAPPING.get(holding_class, "SWING")
    return BUCKETS.get(bucket_name)

def get_bucket_capacity(total_capital: float, holding_class: str) -> dict:
    """
    Checks how much capital is available in the specific bucket and how many open positions there are.
    """
    bucket_name = CLASS_MAPPING.get(holding_class, "SWING")
    config = BUCKETS[bucket_name]
    
    # 1. Total capital allocated to this bucket
    allocated_capital = total_capital * config["capital_allocation_pct"]
    
    # 2. Find currently open positions in this bucket
    open_positions = db.db_execute("SELECT holding_class, quantity, entry_price FROM paper_trades WHERE status = 'OPEN'")
    
    current_used_capital = 0.0
    current_positions_count = 0
    
    for pos in open_positions:
        pos_class = CLASS_MAPPING.get(pos.get("holding_class", "SWING"), "SWING")
        if pos_class == bucket_name:
            current_positions_count += 1
            current_used_capital += float(pos["quantity"] * pos["entry_price"])
            
    remaining_capital = allocated_capital - current_used_capital
    remaining_slots = config["max_positions"] - current_positions_count
    
    return {
        "bucket_name": bucket_name,
        "allocated_capital": allocated_capital,
        "used_capital": current_used_capital,
        "remaining_capital": remaining_capital,
        "open_positions": current_positions_count,
        "max_positions": config["max_positions"],
        "remaining_slots": remaining_slots,
        "can_add": remaining_slots > 0 and remaining_capital > 1000  # min Rs 1000
    }

def calculate_bucketed_position_size(total_capital: float, holding_class: str, entry_price: float, risk_per_trade_pct: float = 0.01, vol_scalar: float = 1.0) -> dict:
    """
    Calculates exact shares to buy based on the bucket's capacity and Kelly constraints.
    Returns: {"quantity": int, "capital_required": float, "approved": bool, "reason": str}
    """
    capacity = get_bucket_capacity(total_capital, holding_class)
    config = get_bucket_config(holding_class)
    
    if not capacity["can_add"]:
        return {
            "quantity": 0,
            "capital_required": 0.0,
            "approved": False,
            "reason": f"Bucket {capacity['bucket_name']} full. (Slots: {capacity['open_positions']}/{capacity['max_positions']}, Rem Cap: {capacity['remaining_capital']})"
        }
        
    # Standard risk sizing (1% of total portfolio risk)
    max_loss_allowed = total_capital * risk_per_trade_pct
    stop_loss_amount = entry_price * config["base_stop_pct"]
    
    if stop_loss_amount <= 0:
        stop_loss_amount = 0.1 # prevent div by zero
        
    risk_based_qty = int(max_loss_allowed / stop_loss_amount)
    
    # Cap by max capital allowed per slot in this bucket
    max_capital_per_slot = capacity["allocated_capital"] / config["max_positions"]
    
    # If remaining capital is less than max per slot, use remaining
    allowed_capital_for_trade = min(max_capital_per_slot, capacity["remaining_capital"])
    
    capital_based_qty = int(allowed_capital_for_trade / entry_price)
    
    # Final quantity is the minimum of risk-based and capital-based
    final_qty = min(risk_based_qty, capital_based_qty)
    
    # Apply Inverse-Volatility Risk Parity Scalar
    # The lower the volatility (e.g. ITC), the higher the vol_scalar, leading to larger position size.
    # The higher the volatility (e.g. ADANIENT), the lower the vol_scalar, mathematically equalizing portfolio risk.
    final_qty = int(final_qty * vol_scalar)
    
    if final_qty <= 0:
        return {
            "quantity": 0,
            "capital_required": 0.0,
            "approved": False,
            "reason": "Calculated quantity is 0 due to risk constraints or lack of capital."
        }
        
    capital_required = final_qty * entry_price
    
    return {
        "quantity": final_qty,
        "capital_required": round(capital_required, 2),
        "approved": True,
        "bucket": capacity["bucket_name"],
        "stop_loss_dist_pct": config["base_stop_pct"],
        "target_dist_pct": config["base_target_pct"],
        "reason": f"Allocated to {capacity['bucket_name']} bucket."
    }
