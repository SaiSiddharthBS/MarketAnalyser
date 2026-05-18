"""
Agent Alpha v4.0 - Weight Evolver
Evolves regime-conditional weights based on model performance.
"""
import json
import logging
import database as db

logger = logging.getLogger(__name__)

DEFAULT_WEIGHTS = {
    "technical": 15,
    "transformer": 25,
    "options_flow": 15,
    "ml_engine": 15,
    "sentiment": 10,
    "insider": 5,
    "macro": 5,
    "momentum": 10
}

def evolve_regime_weights():
    """Called monthly to adjust weights per regime based on prediction_log accuracy."""
    logger.info("🧬 Evolving regime weights...")
    # Get all distinct regimes
    regimes = db.db_execute("SELECT DISTINCT regime FROM prediction_log WHERE outcome IS NOT NULL")
    if not regimes: return
    
    models = ["technical", "transformer", "options_flow", "ml_engine", "sentiment", "insider", "macro", "momentum"]
    
    for r in regimes:
        regime = r["regime"]
        if not regime: continue
        
        predictions = db.db_execute("SELECT model_votes_json, outcome FROM prediction_log WHERE outcome IS NOT NULL AND regime = ?", (regime,))
        if len(predictions) < 20: continue # Need minimum sample size
        
        # Calculate accuracy per model in this regime
        model_stats = {m: {"wins": 0, "total": 0} for m in models}
        for p in predictions:
            try:
                votes = json.loads(p["model_votes_json"])
                for m in models:
                    vote = votes.get(m, 0)
                    if vote != 0:
                        model_stats[m]["total"] += 1
                        if (vote > 0 and p["outcome"] == "WIN") or (vote < 0 and p["outcome"] == "LOSS"):
                            model_stats[m]["wins"] += 1
            except: pass
            
        # Get baseline weights
        base_weights = get_regime_weights(regime)
        new_weights = {}
        
        # Adjust weights
        for m in models:
            stats = model_stats[m]
            if stats["total"] >= 10:
                acc = stats["wins"] / stats["total"]
                # If accuracy > 60%, increase weight by 20%. If < 45%, decrease by 20%.
                adj = 1.2 if acc > 0.6 else (0.8 if acc < 0.45 else 1.0)
                new_weights[m] = base_weights.get(m, DEFAULT_WEIGHTS[m]) * adj
            else:
                new_weights[m] = base_weights.get(m, DEFAULT_WEIGHTS[m])
                
        # Normalize
        total_w = sum(new_weights.values())
        if total_w > 0:
            new_weights = {k: (v / total_w) * 100 for k, v in new_weights.items()}
            
        # Save to DB
        existing = db.db_execute("SELECT id FROM regime_weights WHERE regime = ?", (regime,))
        if existing:
            db.db_execute("UPDATE regime_weights SET weights_json = ?, updated_at = datetime('now') WHERE regime = ?", (json.dumps(new_weights), regime))
        else:
            db.db_execute("INSERT INTO regime_weights (regime, weights_json) VALUES (?, ?)", (regime, json.dumps(new_weights)))
            
    logger.info("✅ Weight evolution complete.")
    
def get_regime_weights(regime: str) -> dict:
    """Load regime-conditional weights from DB and apply Alpha Decay."""
    weights = DEFAULT_WEIGHTS.copy()
    
    # Load custom regime weights if they exist
    res = db.db_execute("SELECT weights_json FROM regime_weights WHERE regime = ?", (regime,))
    if res and res[0]["weights_json"]:
        try:
            weights = json.loads(res[0]["weights_json"])
        except:
            pass
            
    # Apply Alpha Decay Auto-Downweighting
    try:
        from arena.championship import get_leaderboard
        leaderboard = get_leaderboard()
        for l in leaderboard:
            model_key = l["model"].lower().replace(" ", "_")
            if model_key in weights:
                if l["status"] == "SUSPENDED":
                    weights[model_key] = 0
                elif l["status"] == "DECAYING":
                    weights[model_key] = weights[model_key] / 2
                    
        # Normalize weights back to 100
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: (v / total_weight) * 100 for k, v in weights.items()}
    except Exception as e:
        logger.error(f"Failed to apply alpha decay weights: {e}")
            
    return weights
