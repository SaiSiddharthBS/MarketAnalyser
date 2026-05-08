"""
Agent Alpha v2.0 — Error Classification & Analysis Engine
===========================================================
Every losing trade teaches you something — IF you can classify WHY it lost.

Error Categories:
1. GAP EVENT — Overnight gap destroyed the trade
2. REGIME CHANGE — Market regime shifted mid-trade
3. FUNDAMENTAL SHOCK — Earnings miss, regulatory action, etc.
4. MACRO SHOCK — RBI rate surprise, US Fed, geopolitical
5. SECTOR ROTATION — Sector fell while market rallied
6. CROWDING REVERSAL — Too many in same trade, unwinding
7. LIQUIDITY EVENT — Low volume, manipulation, circuit
8. MODEL ERROR — All models agreed but were collectively wrong
9. TIMING ERROR — Direction correct, entry/exit timing wrong
10. UNKNOWN — Cannot categorize

Weekly Report:
If any single category exceeds 25% of all errors → SYSTEMIC issue → ALERT
"""
from collections import Counter
from typing import Dict, Any, List, Optional
from datetime import datetime


class ErrorAnalyzer:
    """Classifies and tracks error patterns in losing trades."""

    ERROR_CATEGORIES = {
        "gap_event": "Overnight gap destroyed the entry",
        "regime_change": "Market regime shifted during the holding period",
        "fundamental_shock": "Earnings, regulatory action, or corporate event",
        "macro_shock": "RBI, Fed, geopolitical, or global macro event",
        "sector_rotation": "Sector underperformed while broad market held",
        "crowding_reversal": "Crowded momentum trade reversed sharply",
        "liquidity_event": "Low volume, price manipulation, or circuit breaker",
        "model_error": "All models agreed but outcome was opposite",
        "timing_error": "Direction was correct but entry/exit timing was wrong",
        "unknown": "Cannot categorize — review manually",
    }

    def __init__(self):
        self.error_log: List[Dict[str, Any]] = []

    def classify_error(self, trade: Dict[str, Any]) -> str:
        """
        Classify a losing trade into one of 10 error categories.

        Args:
            trade: Dict with keys:
                - symbol, signal (BUY/SELL), entry_price, exit_price
                - entry_date, exit_date, actual_return (decimal)
                - day1_open (first day open after entry)
                - regime_at_entry, regime_at_exit
                - had_earnings, had_macro_event
                - model_agreement (how many models agreed)
                - sector_return (sector performance during trade)
                - volume_ratio (RVOL during trade)

        Returns:
            Error category string
        """
        actual_return = trade.get("actual_return", 0)
        signal = trade.get("signal", "BUY")

        # Was this actually a loss?
        if signal == "BUY" and actual_return >= 0:
            return "not_a_loss"
        if signal == "SELL" and actual_return <= 0:
            return "not_a_loss"

        # ─── Check for Gap Event ─────────────────────────────
        day1_open = trade.get("day1_open", 0)
        entry_price = trade.get("entry_price", 0)
        if entry_price > 0 and day1_open > 0:
            gap_pct = abs(day1_open - entry_price) / entry_price
            if gap_pct > 0.02:  # 2%+ gap
                return "gap_event"

        # ─── Check for Fundamental Shock ─────────────────────
        if trade.get("had_earnings", False):
            return "fundamental_shock"

        if trade.get("had_corporate_action", False):
            return "fundamental_shock"

        # ─── Check for Macro Shock ───────────────────────────
        if trade.get("had_macro_event", False):
            return "macro_shock"

        # ─── Check for Regime Change ─────────────────────────
        regime_entry = trade.get("regime_at_entry", "")
        regime_exit = trade.get("regime_at_exit", "")
        if regime_entry and regime_exit and regime_entry != regime_exit:
            return "regime_change"

        # ─── Check for Sector Rotation ───────────────────────
        sector_return = trade.get("sector_return", 0)
        market_return = trade.get("market_return", 0)
        if sector_return < -0.02 and market_return > 0:
            return "sector_rotation"

        # ─── Check for Crowding Reversal ─────────────────────
        momentum_crash_score = trade.get("momentum_crash_score_at_entry", 0)
        if momentum_crash_score > 50:
            return "crowding_reversal"

        # ─── Check for Liquidity Event ───────────────────────
        volume_ratio = trade.get("volume_ratio", 1.0)
        if volume_ratio < 0.3:
            return "liquidity_event"
        if trade.get("hit_circuit", False):
            return "liquidity_event"

        # ─── Check for Model Error ───────────────────────────
        model_agreement = trade.get("model_agreement", 0)
        if model_agreement >= 6:
            return "model_error"

        # ─── Check for Timing Error ──────────────────────────
        # Direction was right within the holding period, but
        # entry or exit was poorly timed
        max_favorable = trade.get("max_favorable_move", 0)
        if signal == "BUY" and max_favorable > 0.02:
            # Stock went up 2%+ during the trade but we still lost
            return "timing_error"

        return "unknown"

    def log_error(self, trade: Dict[str, Any]):
        """Classify and log a losing trade."""
        category = self.classify_error(trade)
        entry = {
            "symbol": trade.get("symbol", ""),
            "date": trade.get("exit_date", datetime.now().strftime("%Y-%m-%d")),
            "category": category,
            "description": self.ERROR_CATEGORIES.get(category, ""),
            "actual_return": trade.get("actual_return", 0),
            "signal": trade.get("signal", ""),
            "model_agreement": trade.get("model_agreement", 0),
        }
        self.error_log.append(entry)
        return entry

    def generate_weekly_report(
        self,
        recent_trades: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Generate the weekly error analysis report.

        If any single category exceeds 25% of all errors → SYSTEMIC ISSUE.

        Args:
            recent_trades: List of recent losing trades

        Returns:
            Dict with: error_counts, total_losses, systemic_issues, recommendations
        """
        if not recent_trades:
            return {"total_losses": 0, "message": "No losses to analyze"}

        # Classify all losses
        categories = []
        for trade in recent_trades:
            actual = trade.get("actual_return", 0)
            signal = trade.get("signal", "BUY")
            is_loss = (signal == "BUY" and actual < 0) or (signal == "SELL" and actual > 0)
            if is_loss:
                cat = self.classify_error(trade)
                categories.append(cat)

        if not categories:
            return {"total_losses": 0, "message": "No losses in recent trades"}

        error_counts = Counter(categories)
        total = len(categories)

        # Detect systemic issues
        systemic = []
        recommendations = []

        for category, count in error_counts.items():
            pct = count / total
            if pct > 0.25:
                systemic.append({
                    "category": category,
                    "count": count,
                    "pct": round(pct * 100, 1),
                    "description": self.ERROR_CATEGORIES.get(category, ""),
                })

                # Generate specific recommendation
                rec = self._get_recommendation(category, pct)
                if rec:
                    recommendations.append(rec)

        return {
            "total_losses": total,
            "error_counts": dict(error_counts),
            "error_percentages": {k: round(v / total * 100, 1) for k, v in error_counts.items()},
            "systemic_issues": systemic,
            "has_systemic_issue": len(systemic) > 0,
            "recommendations": recommendations,
            "report_date": datetime.now().strftime("%Y-%m-%d"),
        }

    def _get_recommendation(self, category: str, pct: float) -> Optional[str]:
        """Generate actionable recommendation for a systemic error pattern."""
        recs = {
            "gap_event": f"Gap events causing {pct:.0%} of losses → increase pre-market gap risk monitoring, consider reducing overnight positions",
            "regime_change": f"Regime changes causing {pct:.0%} of losses → HMM classifier needs recalibration, consider faster regime detection",
            "fundamental_shock": f"Fundamental shocks causing {pct:.0%} of losses → strengthen earnings blackout, widen pre-event position reduction window",
            "macro_shock": f"Macro events causing {pct:.0%} of losses → expand macro calendar coverage, increase pre-event suppression",
            "sector_rotation": f"Sector rotation causing {pct:.0%} of losses → increase sector diversification, add relative strength filter",
            "crowding_reversal": f"Crowding reversals causing {pct:.0%} of losses → lower momentum crash risk threshold, earlier position reduction",
            "liquidity_event": f"Liquidity events causing {pct:.0%} of losses → increase minimum volume filter, exclude illiquid stocks",
            "model_error": f"Collective model error causing {pct:.0%} of losses → review signal weights, check for overfitting, recalibrate in current regime",
            "timing_error": f"Timing errors causing {pct:.0%} of losses → review entry criteria, consider wider initial stops",
        }
        return recs.get(category)


# Global singleton
error_analyzer = ErrorAnalyzer()
