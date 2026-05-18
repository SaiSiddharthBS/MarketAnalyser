"""
Agent Alpha v4.0 - Self-Learner
Error pattern mining & automated rule generation based on historical predictions.
"""
import json
import logging
from datetime import datetime
import database as db

logger = logging.getLogger(__name__)

def mine_error_patterns():
    """Run weekly to discover which conditions cause losses and generate rules."""
    logger.info("🧠 Mining error patterns from prediction history...")
    
    count_res = db.db_execute("SELECT COUNT(*) as count FROM prediction_log WHERE outcome IS NOT NULL")
    if not count_res or count_res[0]["count"] < 50:
        logger.info("Not enough resolved predictions to mine rules. Need at least 50.")
        return
        
    predictions = db.db_execute("SELECT * FROM prediction_log WHERE outcome IS NOT NULL")
    stats = {} 
    
    for p in predictions:
        reg = p["regime"]
        day = p["day_of_week"]
        is_win = (p["outcome"] == "WIN")
        
        reg_key = f"regime_{reg}"
        if reg_key not in stats: stats[reg_key] = {"wins": 0, "losses": 0}
        
        day_key = f"day_{day}"
        if day_key not in stats: stats[day_key] = {"wins": 0, "losses": 0}
        
        if is_win:
            stats[reg_key]["wins"] += 1
            stats[day_key]["wins"] += 1
        else:
            stats[reg_key]["losses"] += 1
            stats[day_key]["losses"] += 1
            
        # VIX Binning (10-15, 15-20, 20-25, 25+)
        vix = p.get("vix_level", 0)
        if vix:
            vix_bin = "vix_<15" if vix < 15 else "vix_15-20" if vix < 20 else "vix_20-25" if vix < 25 else "vix_>25"
            if vix_bin not in stats: stats[vix_bin] = {"wins": 0, "losses": 0}
            if is_win: stats[vix_bin]["wins"] += 1
            else: stats[vix_bin]["losses"] += 1
            
    today = datetime.now().strftime('%Y-%m-%d')
    new_rules = 0
            
    for key, data in stats.items():
        total = data["wins"] + data["losses"]
        if total < 20: continue 
        
        win_rate = data["wins"] / total
        if win_rate < 0.40:
            if key.startswith("day_"):
                day = key.replace("day_", "")
                rule_cond = {"day_of_week": day, "conviction_not": "ULTRA"}
                rule_action = {"skip": True}
                
                existing = db.db_execute("SELECT id FROM learned_rules WHERE condition_json = ?", (json.dumps(rule_cond),))
                if not existing:
                    db.db_execute("""
                        INSERT INTO learned_rules (rule_type, condition_json, action_json, confidence, sample_size, discovered_date)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, ("TRADE_SKIP", json.dumps(rule_cond), json.dumps(rule_action), 1.0 - win_rate, total, today))
                    new_rules += 1
                    logger.info(f"Generated new rule: Skip non-ULTRA trades on {day}")
                    
            elif key.startswith("regime_"):
                reg = key.replace("regime_", "")
                rule_cond = {"regime": reg}
                rule_action = {"require_conviction": "ULTRA"}
                
                existing = db.db_execute("SELECT id FROM learned_rules WHERE condition_json = ?", (json.dumps(rule_cond),))
                if not existing:
                    db.db_execute("""
                        INSERT INTO learned_rules (rule_type, condition_json, action_json, confidence, sample_size, discovered_date)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, ("REQUIRE_ULTRA", json.dumps(rule_cond), json.dumps(rule_action), 1.0 - win_rate, total, today))
                    new_rules += 1
                    logger.info(f"Generated new rule: Require ULTRA conviction in {reg} regime")
                    
            elif key.startswith("vix_"):
                vix_range = key.replace("vix_", "")
                rule_cond = {"vix_range": vix_range}
                rule_action = {"reduce_weight": {"momentum": 0.5}} # Halve momentum weight as spec
                
                existing = db.db_execute("SELECT id FROM learned_rules WHERE condition_json = ?", (json.dumps(rule_cond),))
                if not existing:
                    db.db_execute("""
                        INSERT INTO learned_rules (rule_type, condition_json, action_json, confidence, sample_size, discovered_date)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, ("VIX_THRESHOLD", json.dumps(rule_cond), json.dumps(rule_action), 1.0 - win_rate, total, today))
                    new_rules += 1
                    logger.info(f"Learned Rule: Halve momentum when VIX is {vix_range} due to low win rate ({win_rate*100:.1f}%)")
                    
    logger.info(f"Mining complete. Discovered {new_rules} new rules.")


def apply_learned_rules(signal_context: dict) -> dict:
    """
    Called during signal generation. Applies discovered rules.
    """
    rules = db.db_execute("SELECT * FROM learned_rules WHERE is_active = 1")
    modifiers = {"skip": False, "require_conviction": None, "weight_modifiers": {}}
    if not rules: return modifiers
    
    for rule in rules:
        cond = json.loads(rule["condition_json"])
        action = json.loads(rule["action_json"])
        
        match = True
        for k, v in cond.items():
            if k == "conviction_not":
                if signal_context.get("conviction") == v:
                    match = False
            elif k == "vix_range":
                vix = signal_context.get("vix_level", 0)
                if v == "<15" and vix >= 15: match = False
                elif v == "15-20" and (vix < 15 or vix >= 20): match = False
                elif v == "20-25" and (vix < 20 or vix >= 25): match = False
                elif v == ">25" and vix < 25: match = False
            elif signal_context.get(k) != v:
                match = False
                
        if match:
            if action.get("skip"):
                modifiers["skip"] = True
            if action.get("require_conviction"):
                modifiers["require_conviction"] = action["require_conviction"]
            if action.get("reduce_weight"):
                for mod_k, mod_v in action["reduce_weight"].items():
                    modifiers["weight_modifiers"][mod_k] = mod_v
                
    return modifiers

if __name__ == "__main__":
    mine_error_patterns()
    try:
        from arena.weight_evolver import evolve_regime_weights
        evolve_regime_weights()
    except Exception as e:
        logger.error(f"Failed to evolve regime weights: {e}")
