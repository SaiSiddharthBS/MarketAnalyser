"""
Agent Alpha v2.0 — Insider/SAST Signal Model (Model 8)
=======================================================
Weight in ensemble: 10%

SEBI mandates disclosure of all insider trades within 2 trading days.
Promoter buying in open market is the HIGHEST conviction signal possible —
they know their own company better than anyone.

Data Sources:
- BSE corporate filings (SAST disclosures)
- NSE insider trading disclosures
- Promoter/KMP trade notifications

Signal Logic:
- Promoter buying > ₹10 Cr = VERY STRONG BUY (+6)
- Promoter buying > ₹1 Cr = STRONG BUY (+4)
- Any promoter buying = BUY (+2)
- Multiple promoters selling = WARNING (-3)
- KMP cluster buying (3+ insiders) = STRONG BUY (+3)
- Entity crossing 5% threshold = Potential acquisition (+4)
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


def calculate_insider_signal(
    disclosures: List[Dict[str, Any]],
    symbol: str,
    lookback_days: int = 30,
) -> Dict[str, Any]:
    """
    Calculate insider/SAST trading signal from disclosure data.

    Args:
        disclosures: List of insider trade disclosures with keys:
            - symbol, category (PROMOTER/KMP/RELATED), transaction_type (BUY/SELL),
              value (₹), disclosure_date, entity_name
        symbol: Stock symbol to filter for
        lookback_days: Days to look back for recent disclosures

    Returns:
        Dict with: signal, confidence, direction, insider_score, details
    """
    if not disclosures:
        return {"signal": "NEUTRAL", "confidence": 0, "direction": 0, "insider_score": 0}

    cutoff = datetime.now() - timedelta(days=lookback_days)

    # Filter relevant disclosures
    recent = []
    for d in disclosures:
        d_sym = d.get("symbol", "").upper()
        if d_sym != symbol.upper():
            continue
        d_date = d.get("disclosure_date")
        if d_date:
            if isinstance(d_date, str):
                try:
                    d_date = datetime.strptime(d_date, "%Y-%m-%d")
                except (ValueError, TypeError):
                    continue
            if d_date < cutoff:
                continue
        recent.append(d)

    if not recent:
        return {"signal": "NEUTRAL", "confidence": 0, "direction": 0, "insider_score": 0}

    # ─── Categorize Transactions ─────────────────────────────
    promoter_buys = [d for d in recent if d.get("category", "").upper() == "PROMOTER" and d.get("transaction_type", "").upper() == "BUY"]
    promoter_sells = [d for d in recent if d.get("category", "").upper() == "PROMOTER" and d.get("transaction_type", "").upper() == "SELL"]
    kmp_buys = [d for d in recent if d.get("category", "").upper() == "KMP" and d.get("transaction_type", "").upper() == "BUY"]
    threshold_crossings = [d for d in recent if d.get("category", "").upper() in ("SAST", "THRESHOLD_CROSSING")]

    insider_score = 0
    details = []

    # ─── Promoter Buying (Highest conviction) ────────────────
    if promoter_buys:
        total_buy_value = sum(d.get("value", 0) for d in promoter_buys)

        if total_buy_value >= 10_00_00_000:  # ₹10 Crore+
            insider_score += 6
            details.append(f"Promoter bought ₹{total_buy_value/1e7:.1f}Cr (VERY STRONG)")
        elif total_buy_value >= 1_00_00_000:  # ₹1 Crore+
            insider_score += 4
            details.append(f"Promoter bought ₹{total_buy_value/1e7:.1f}Cr (STRONG)")
        else:
            insider_score += 2
            details.append(f"Promoter bought ₹{total_buy_value/1e5:.1f}L")

    # ─── Promoter Selling (Nuanced) ──────────────────────────
    # Single promoter selling = could be planned, not bearish
    # Multiple promoters selling = concern
    if len(promoter_sells) >= 3:
        insider_score -= 3
        total_sell = sum(d.get("value", 0) for d in promoter_sells)
        details.append(f"{len(promoter_sells)} promoters selling (total ₹{total_sell/1e7:.1f}Cr) — CONCERN")
    elif len(promoter_sells) == 1:
        details.append("Single promoter sale — likely planned disposal")

    # ─── KMP Cluster Buying ──────────────────────────────────
    if len(kmp_buys) >= 3:
        insider_score += 3
        details.append(f"{len(kmp_buys)} KMPs buying simultaneously — VERY BULLISH")
    elif len(kmp_buys) >= 1:
        insider_score += 1
        details.append(f"KMP insider buying detected")

    # ─── Threshold Crossings (SAST) ──────────────────────────
    for tc in threshold_crossings:
        threshold = tc.get("threshold_pct", 0)
        direction = tc.get("direction", "unknown")
        if direction == "crossing_up" and threshold >= 5:
            insider_score += 4
            details.append(f"Entity crossed {threshold}% threshold — potential acquisition target")

    # ─── Signal Generation ───────────────────────────────────
    if insider_score >= 5:
        signal, direction = "BUY", 1
        confidence = min(95, 60 + insider_score * 5)
    elif insider_score >= 3:
        signal, direction = "BUY", 1
        confidence = min(80, 45 + insider_score * 7)
    elif insider_score >= 1:
        signal, direction = "BUY", 1
        confidence = min(60, 30 + insider_score * 10)
    elif insider_score <= -3:
        signal, direction = "SELL", -1
        confidence = min(80, 40 + abs(insider_score) * 8)
    elif insider_score <= -1:
        signal, direction = "SELL", -1
        confidence = min(60, 30 + abs(insider_score) * 10)
    else:
        signal, direction = "NEUTRAL", 0
        confidence = 30

    return {
        "signal": signal,
        "confidence": confidence,
        "direction": direction,
        "insider_score": insider_score,
        "promoter_buys_count": len(promoter_buys),
        "promoter_sells_count": len(promoter_sells),
        "kmp_buys_count": len(kmp_buys),
        "threshold_crossings": len(threshold_crossings),
        "details": details,
    }
