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
    
    if net_pnl > 0:
        autopsy = f"Trade won. Reason: {exit_reason}. The model signals correctly captured the momentum."
    else:
        autopsy = f"Trade lost. Reason: {exit_reason}. The trade failed to reach the target. Further analysis required."
        
    db.db_execute("""
        UPDATE paper_trades SET autopsy_json = ? WHERE id = ?
    """, (json.dumps({"summary": autopsy}), trade_id))
    logger.info(f"Generated autopsy for trade {trade_id}")
