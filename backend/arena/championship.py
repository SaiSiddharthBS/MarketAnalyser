"""
Agent Alpha v4.0 - Championship Leaderboard
Tracks individual model performance and ranks them.
"""
import logging
import database as db
from analysis.alpha_decay import AlphaDecayMonitor

logger = logging.getLogger(__name__)
models_list = ["technical", "transformer", "short_term_nn", "options_flow", "fno_bias", "ml_engine", "sentiment", "insider", "macro", "momentum", "value", "quality", "earnings", "smart_money", "stat_arb"]
decay_monitor = AlphaDecayMonitor(signal_names=models_list)

def get_leaderboard():
    """Returns the championship leaderboard stats for the frontend."""
    # Read the AlphaDecayMonitor stats directly from the database or via the monitor.
    # AlphaDecayMonitor tracks 60d rolling accuracy.
    
    # We can calculate this from prediction_log as well
    models = ["technical", "transformer", "short_term_nn", "options_flow", "fno_bias", "ml_engine", "sentiment", "insider", "macro", "momentum", "value", "quality", "earnings", "smart_money", "stat_arb"]
    
    leaderboard = []
    
    for model in models:
        # A simple query to get wins/losses where this model voted for the outcome within last 60 days
        # Since model_votes_json is JSON, we fetch and process
        import datetime
        cutoff = (datetime.datetime.now() - datetime.timedelta(days=60)).strftime('%Y-%m-%d')
        predictions = db.db_execute("SELECT model_votes_json, outcome FROM prediction_log WHERE outcome IS NOT NULL AND signal_date >= ?", (cutoff,))
        
        wins = 0
        total = 0
        
        for p in predictions:
            try:
                import json
                votes = json.loads(p["model_votes_json"])
                vote = votes.get(model, 0)
                if vote != 0:
                    total += 1
                    if (vote > 0 and p["outcome"] == "WIN") or (vote < 0 and p["outcome"] == "LOSS"):
                        wins += 1
            except:
                pass
                
        accuracy = (wins / total * 100) if total > 0 else 0
        
        status = "HEALTHY"
        if accuracy < 45 and total >= 10:
            status = "DECAYING"
        if accuracy < 35 and total >= 20:
            status = "SUSPENDED"
            
        from arena.weight_evolver import DEFAULT_WEIGHTS
        try:
            from analysis.regime import detect_market_regime
            cur_regime = detect_market_regime().get("regime", "unknown")
        except:
            cur_regime = "unknown"
            
        # Read from DB directly to avoid infinite recursion with weight_evolver
        res = db.db_execute("SELECT weights_json FROM regime_weights WHERE regime = ?", (cur_regime,))
        cur_weights = DEFAULT_WEIGHTS.copy()
        if res and res[0]["weights_json"]:
            try:
                import json
                cur_weights = json.loads(res[0]["weights_json"])
            except:
                pass
        
        leaderboard.append({
            "model": model.replace("_", " ").title(),
            "accuracy": round(accuracy, 2),
            "trades": total,
            "status": status,
            "current_weight": cur_weights.get(model, DEFAULT_WEIGHTS.get(model, 0)),
            "base_weight": DEFAULT_WEIGHTS.get(model, 0),
            "sparkline": "▃▅▆▇" if status == "HEALTHY" else "▇▆▅▃"
        })
        
    leaderboard.sort(key=lambda x: x["accuracy"], reverse=True)
    return leaderboard
