import logging
import pandas as pd
from typing import Dict, Any
from data.fundamentals_fetcher import fetch_fundamentals

logger = logging.getLogger(__name__)

def evaluate_value_factor(fundamentals: dict) -> dict:
    """
    Value Factor: Long stocks with low P/E and low P/B ratios.
    """
    score = 0
    reasons = []
    
    pe = fundamentals.get("pe", 0)
    pb = fundamentals.get("pb", 0)
    
    if pe > 0 and pe < 15:
        score += 60
        reasons.append(f"Strong Value: Low P/E ({pe:.1f})")
    elif pe > 0 and pe < 25:
        score += 30
        reasons.append(f"Moderate Value: Fair P/E ({pe:.1f})")
    elif pe > 40:
        score -= 40
        reasons.append(f"Overvalued: High P/E ({pe:.1f})")
        
    if pb > 0 and pb < 2:
        score += 40
        reasons.append(f"Strong Value: Low P/B ({pb:.1f})")
    elif pb > 5:
        score -= 20
        reasons.append(f"Overvalued: High P/B ({pb:.1f})")
        
    score = max(-100, min(100, score))
    signal = "BULLISH" if score >= 50 else "BEARISH" if score <= -30 else "NEUTRAL"
    
    return {"signal": signal, "score": score, "reasons": reasons}

def evaluate_quality_factor(fundamentals: dict) -> dict:
    """
    Quality Factor: Long stocks with high ROE, low debt, and strong margins.
    """
    score = 0
    reasons = []
    
    roe = fundamentals.get("roe", 0)
    debt = fundamentals.get("debt_to_equity", 0)
    
    # ROE is often delivered as a decimal (e.g., 0.15 for 15%)
    if roe > 0.15:
        score += 60
        reasons.append(f"High Quality: Strong ROE ({roe*100:.1f}%)")
    elif roe < 0.05:
        score -= 50
        reasons.append(f"Low Quality: Weak ROE ({roe*100:.1f}%)")
        
    # Debt to Equity (usually 0-200+)
    if debt < 50:
        score += 40
        reasons.append(f"High Quality: Low Debt/Equity ({debt:.1f})")
    elif debt > 150:
        score -= 30
        reasons.append(f"Risk: High Debt/Equity ({debt:.1f})")
        
    score = max(-100, min(100, score))
    signal = "BULLISH" if score >= 50 else "BEARISH" if score <= -30 else "NEUTRAL"
    
    return {"signal": signal, "score": score, "reasons": reasons}

def evaluate_earnings_surprise_factor(fundamentals: dict) -> dict:
    """
    Earnings Surprise: Post-earnings drift anomaly.
    """
    score = 0
    reasons = []
    
    growth = fundamentals.get("eps_growth_est", 0)
    
    if growth > 0.15:
        score += 100
        reasons.append(f"Strong Growth Est: EPS expected to grow {growth*100:.1f}%")
    elif growth > 0.05:
        score += 50
        reasons.append(f"Moderate Growth Est: EPS expected to grow {growth*100:.1f}%")
    elif growth < 0:
        score -= 50
        reasons.append(f"Negative Growth Est: EPS expected to shrink {growth*100:.1f}%")
        
    score = max(-100, min(100, score))
    signal = "BULLISH" if score >= 50 else "BEARISH" if score <= -30 else "NEUTRAL"
    
    return {"signal": signal, "score": score, "reasons": reasons}

def get_all_factors(symbol: str) -> dict:
    fundamentals = fetch_fundamentals(symbol)
    if not fundamentals:
        return {
            "value": {"signal": "NEUTRAL", "score": 0, "reasons": ["No fundamental data"]},
            "quality": {"signal": "NEUTRAL", "score": 0, "reasons": ["No fundamental data"]},
            "earnings": {"signal": "NEUTRAL", "score": 0, "reasons": ["No fundamental data"]}
        }
        
    return {
        "value": evaluate_value_factor(fundamentals),
        "quality": evaluate_quality_factor(fundamentals),
        "earnings": evaluate_earnings_surprise_factor(fundamentals)
    }
