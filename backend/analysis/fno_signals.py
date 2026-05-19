import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from data.options_fetcher import fetch_options_chain, calculate_pcr

logger = logging.getLogger(__name__)

def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    if out != out:
        return default
    return out

def classify_buildup(price_change: float, oi_change: float) -> str:
    """Classify the dominant OI buildup for a single strike/option."""
    if price_change > 0 and oi_change > 0:
        return "long_buildup"
    elif price_change < 0 and oi_change > 0:
        return "short_buildup"
    elif price_change > 0 and oi_change < 0:
        return "short_covering"
    elif price_change < 0 and oi_change < 0:
        return "long_unwinding"
    return "neutral"

def _dominant_buildup(options_data: List[Dict]) -> dict[str, Any]:
    counts: dict[str, float] = {}
    
    for row in options_data:
        ce = row.get("CE", {})
        pe = row.get("PE", {})
        
        # Analyze Calls
        if ce:
            price_change = _to_float(ce.get("change"), 0.0)
            oi_change = _to_float(ce.get("changeinOpenInterest"), 0.0)
            if oi_change != 0:
                pattern = classify_buildup(price_change, oi_change)
                weight = abs(oi_change)
                counts[pattern] = counts.get(pattern, 0.0) + max(weight, 1.0)
                
        # Analyze Puts
        if pe:
            price_change = _to_float(pe.get("change"), 0.0)
            oi_change = _to_float(pe.get("changeinOpenInterest"), 0.0)
            if oi_change != 0:
                pattern = classify_buildup(price_change, oi_change)
                weight = abs(oi_change)
                counts[pattern] = counts.get(pattern, 0.0) + max(weight, 1.0)

    if not counts:
        return {"classification": "neutral", "confidence": 0.0, "distribution": {}}
        
    total = sum(counts.values())
    label, value = max(counts.items(), key=lambda item: item[1])
    return {
        "classification": label,
        "confidence": round(value / total, 4) if total else 0.0,
        "distribution": {key: round(val / total, 4) for key, val in sorted(counts.items())},
    }

def _directional_bias(pcr_oi: float, buildup: str) -> float:
    score = 0.0
    if pcr_oi > 1.15:
        score += 0.35
    elif 0.0 < pcr_oi < 0.7:
        score -= 0.35
    if buildup == "long_buildup":
        score += 0.30
    elif buildup == "short_buildup":
        score -= 0.30
    elif buildup == "short_covering":
        score += 0.15
    elif buildup == "long_unwinding":
        score -= 0.15
    return round(max(-1.0, min(1.0, score)), 4)

def get_option_chain_signals(symbol: str) -> dict[str, Any]:
    """Fetch option chain and extract signals for Agent Alpha."""
    symbol_u = symbol.strip().upper()
    
    # Only NSE supported for now
    if not (symbol_u.endswith(".NS") or symbol_u in ["NIFTY", "BANKNIFTY"]):
        if not "." in symbol_u:
            symbol_u = "NIFTY" if symbol_u == "^NSEI" else symbol_u
    
    try:
        # 1. Fetch from NSE via our internal fetcher
        chain_response = fetch_options_chain(symbol_u)
        if not chain_response or "data" not in chain_response:
            return {"available": False, "reason": "No data from NSE"}
            
        options_data = chain_response.get("data", [])
        
        # 2. Extract PCR
        pcr_data = calculate_pcr(options_data)
        pcr_oi = _to_float(pcr_data.get("pcr_oi"), 1.0)
        
        # 3. Extract Buildup
        buildup = _dominant_buildup(options_data)
        
        # Note: True IV percentiles require historical IV databases. 
        # Using a proxy from our existing models or defaulting to 50 for now.
        iv_percentile = 50.0  
        
        return {
            "symbol": symbol_u,
            "available": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pcr_oi": pcr_oi,
            "pcr_signal": pcr_data.get("interpretation", "Neutral"),
            "oi_buildup": buildup["classification"],
            "oi_buildup_confidence": buildup["confidence"],
            "oi_buildup_distribution": buildup["distribution"],
            "iv_percentile": iv_percentile,
            "directional_bias": _directional_bias(pcr_oi, str(buildup["classification"])),
        }
    except Exception as exc:
        logger.error(f"F&O Signal error for {symbol_u}: {exc}")
        return {
            "symbol": symbol_u,
            "available": False,
            "reason": "provider_unavailable",
            "error": str(exc)[:200]
        }


