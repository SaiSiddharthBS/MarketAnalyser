"""
Agent Alpha v4.0 - Trade Autopsy Engine
Analyzes closed paper trades and determines why they won or lost.
"""
import json
import logging
import database as db

logger = logging.getLogger(__name__)

def generate_autopsy(trade_id: int):
    """Generate a post-mortem analysis for a closed trade."""
    res = db.db_execute("SELECT * FROM paper_trades WHERE id = ?", (trade_id,))
    if not res:
        return
        
    trade = dict(res[0])
    symbol = trade["symbol"]
    net_pnl = trade["net_pnl"]
    exit_reason = trade["exit_reason"]
    trade_type = trade.get("trade_type", "LONG")
    entry_price = trade.get("entry_price", 0)
    exit_price = trade.get("exit_price", 0)
    ret_pct = trade.get("return_pct", 0)
    regime = trade.get("regime_at_entry", "Unknown")
    
    # Calculate days held if dates are available
    days_held = "a short period"
    try:
        from datetime import datetime
        d1 = datetime.strptime(trade["entry_date"], '%Y-%m-%d')
        d2 = datetime.strptime(trade["exit_date"], '%Y-%m-%d')
        diff = (d2 - d1).days
        days_held = f"{diff} days" if diff > 0 else "the same trading session"
    except Exception:
        pass

    # Build dynamic autopsy
    if exit_reason in ("TARGET_HIT", "TARGET_HIT_LIVE"):
        autopsy = f"Perfect Execution: This {trade_type} trade on {symbol} successfully captured momentum in a '{regime}' market. The price reached our target of ₹{exit_price:.2f} within {days_held}, yielding a solid +{ret_pct:.2f}% return."
    elif exit_reason in ("SL_HIT", "SL_HIT_LIVE"):
        if net_pnl > 0:
            autopsy = f"Trailing Exit: The {trade_type} trade on {symbol} was closed at our trailing stop of ₹{exit_price:.2f} after {days_held}. We secured a positive return of +{ret_pct:.2f}% before the trend could reverse."
        else:
            autopsy = f"Risk Management Triggered: The {trade_type} setup on {symbol} invalidated when the price breached our stop-loss at ₹{exit_price:.2f}. We cut losses at {ret_pct:.2f}% to preserve capital during the '{regime}' regime."
    elif exit_reason == "TIMEOUT_15D":
        autopsy = f"Time Stop: The {trade_type} trade on {symbol} failed to reach either target or stop-loss after 15 days. Exited at ₹{exit_price:.2f} to free up capital for better opportunities."
    else:
        autopsy = f"Manual/System Exit: Trade closed at ₹{exit_price:.2f} resulting in a {ret_pct:.2f}% move."
        
    db.db_execute("""
        UPDATE paper_trades SET autopsy_json = ? WHERE id = ?
    """, (json.dumps({"summary": autopsy}), trade_id))
    logger.info(f"Generated autopsy for trade {trade_id}")
