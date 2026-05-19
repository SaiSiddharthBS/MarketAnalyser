"""
Agent Alpha v2.0 — Hard Veto Engine
=====================================
These rules CANNOT be overridden by ANY technical or ML signal. They are ABSOLUTE.

When a veto fires, the signal is forced to STAND ASIDE regardless of what
the 8 ensemble models say. This is what separates a surviving system from 
a blown-up one.

Hard vetoes exist because certain market conditions make ALL predictive
models unreliable — no amount of technical analysis can predict an
overnight regulatory action or a mass institutional exodus.

Every veto is logged with timestamps for audit trail and SEBI compliance.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pytz

IST = pytz.timezone("Asia/Kolkata")


class VetoEngine:
    """
    Absolute rule engine that overrides all signals.
    No ensemble score, no ML probability, no technical pattern
    can override a hard veto. Period.
    """

    def __init__(self):
        self.active_vetoes: List[Dict[str, Any]] = []
        self.veto_history: List[Dict[str, Any]] = []

    def check_all_vetoes(
        self,
        symbol: str,
        stock_data: Dict[str, Any],
        market_data: Dict[str, Any],
        portfolio_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Run ALL veto checks for a stock. If ANY fires, signal = STAND ASIDE.

        Args:
            symbol: Stock symbol
            stock_data: Per-stock data (pledging, earnings, circuits, SEBI flags)
            market_data: Market-wide data (FII flow, VIX, regime, SGX gap)
            portfolio_data: Portfolio state (drawdown, existing positions)

        Returns:
            Dict with: vetoed (bool), active_vetoes (list), signal_override
        """
        active = []

        # ─── STOCK-LEVEL VETOES (Block BUY for this specific stock) ──

        # Veto 1: Promoter pledging > 40% AND increasing QoQ
        pledging_pct = stock_data.get("promoter_pledging_pct", 0)
        pledging_increasing = stock_data.get("promoter_pledging_increasing_qoq", False)
        if pledging_pct > 40 and pledging_increasing:
            active.append(self._create_veto(
                symbol, "PROMOTER_PLEDGING",
                f"Promoter pledging at {pledging_pct:.1f}% and increasing QoQ",
                severity="HIGH",
                duration_days=180,  # Block for 2 quarters
            ))

        # Veto 1b: Pledging increased by >10% in single quarter
        pledging_increase_qoq = stock_data.get("promoter_pledging_change_qoq_pct", 0)
        if pledging_increase_qoq > 10:
            active.append(self._create_veto(
                symbol, "PROMOTER_PLEDGING_SPIKE",
                f"Promoter pledging increased {pledging_increase_qoq:.1f}% in one quarter",
                severity="HIGH",
                duration_days=180,
            ))

        # Veto 2: Earnings announcement within 3 trading days
        days_to_earnings = stock_data.get("days_to_earnings", 999)
        if days_to_earnings <= 3:
            active.append(self._create_veto(
                symbol, "EARNINGS_BLACKOUT",
                f"Earnings announcement in {days_to_earnings} trading day(s)",
                severity="MEDIUM",
                duration_days=days_to_earnings + 2,  # Block through 2 days post-earnings
            ))

        # Veto 3: Stock hit lower circuit in past 10 days
        lower_circuit_in_10d = stock_data.get("lower_circuit_in_10d", False)
        if lower_circuit_in_10d:
            active.append(self._create_veto(
                symbol, "LOWER_CIRCUIT",
                "Stock hit lower circuit in the past 10 trading days",
                severity="HIGH",
                duration_days=10,
            ))

        # Veto 4: SEBI investigation or regulatory action
        sebi_flag = stock_data.get("sebi_investigation", False)
        if sebi_flag:
            active.append(self._create_veto(
                symbol, "SEBI_INVESTIGATION",
                "Stock is under SEBI investigation or has regulatory notice",
                severity="CRITICAL",
                duration_days=90,
            ))

        # Veto 5: ASM/ESM list
        asm_esm = stock_data.get("in_asm_esm_list", False)
        if asm_esm:
            active.append(self._create_veto(
                symbol, "ASM_ESM_LIST",
                "Stock is on Additional/Enhanced Surveillance Measure list",
                severity="HIGH",
                duration_days=90,
            ))

        # Veto 6: Credit rating downgrade (significant — 2+ steps)
        credit_downgrade = stock_data.get("credit_downgrade_steps", 0)
        if credit_downgrade >= 2:
            active.append(self._create_veto(
                symbol, "CREDIT_DOWNGRADE",
                f"Credit rating downgraded by {credit_downgrade} steps",
                severity="HIGH",
                duration_days=90,
            ))
            
        # Veto 6b: F&O Options Warning (High IV + Short Buildup)
        try:
            from analysis.fno_signals import get_option_chain_signals
            fno_data = get_option_chain_signals(symbol)
            if fno_data.get("available"):
                iv_pct = fno_data.get("iv_percentile", 0)
                buildup = fno_data.get("oi_buildup", "")
                if iv_pct > 85 and buildup == "short_buildup":
                    active.append(self._create_veto(
                        symbol, "OPTIONS_DANGER",
                        f"Extreme options volatility (IV %ile > 85) combined with Short Buildup",
                        severity="HIGH",
                        duration_days=2,
                    ))
        except Exception:
            pass

        # ─── MARKET-LEVEL VETOES (Block ALL buys) ────────────

        # Veto 7: FII net selling > ₹5000 Cr on previous day
        fii_hard_veto = market_data.get("fii_hard_veto_active", False)
        if fii_hard_veto:
            active.append(self._create_veto(
                symbol, "FII_MASS_SELLING",
                market_data.get("fii_hard_veto_reason", "FII net selling > ₹5000Cr"),
                severity="HIGH",
                duration_days=2,
            ))

        # Veto 8: Regime = State 4 (Crisis/Crash)
        regime_state = market_data.get("regime_state", "unknown")
        if regime_state in ("crisis", "state_4", "CRISIS"):
            active.append(self._create_veto(
                symbol, "CRISIS_REGIME",
                f"Market regime is CRISIS (State 4) — all buys vetoed",
                severity="CRITICAL",
                duration_days=0,  # Active as long as regime persists
            ))

        # Veto 9: VIX risen > 30% in 5 days
        vix_5d_change_pct = market_data.get("vix_5d_change_pct", 0)
        if vix_5d_change_pct > 30:
            active.append(self._create_veto(
                symbol, "VIX_SPIKE",
                f"VIX spiked {vix_5d_change_pct:.1f}% in 5 days (threshold: 30%)",
                severity="HIGH",
                duration_days=3,
            ))

        # Veto 10: Pre-market SGX Nifty gap down > 1.5%
        sgx_gap_pct = market_data.get("sgx_nifty_gap_pct", 0)
        if sgx_gap_pct < -1.5:
            active.append(self._create_veto(
                symbol, "SGX_GAP_DOWN",
                f"SGX Nifty gap down {sgx_gap_pct:.2f}% — suppress all buy signals",
                severity="MEDIUM",
                duration_days=1,
            ))

        # ─── PORTFOLIO-LEVEL VETOES ──────────────────────────

        if portfolio_data:
            # Veto 11: Portfolio drawdown > 20% → LIQUIDATE ALL
            drawdown_pct = portfolio_data.get("drawdown_from_peak_pct", 0)
            if drawdown_pct > 20:
                active.append(self._create_veto(
                    symbol, "PORTFOLIO_DRAWDOWN",
                    f"Portfolio drawdown {drawdown_pct:.1f}% from peak (max: 20%)",
                    severity="CRITICAL",
                    duration_days=0,
                    action="EXIT_ALL",
                ))

            # Veto 12: VIX > 40 → Go to 100% cash
            vix_level = market_data.get("vix", 0)
            if vix_level > 40:
                active.append(self._create_veto(
                    symbol, "VIX_PANIC",
                    f"VIX at {vix_level:.1f} — systemic crisis — go to 100% cash",
                    severity="CRITICAL",
                    duration_days=0,
                    action="EXIT_ALL",
                ))

        # ─── RESULT ──────────────────────────────────────────
        vetoed = len(active) > 0

        # Log all vetoes
        for v in active:
            self.veto_history.append(v)

        self.active_vetoes = active

        # Determine highest severity
        severities = [v["severity"] for v in active]
        max_severity = "NONE"
        if "CRITICAL" in severities:
            max_severity = "CRITICAL"
        elif "HIGH" in severities:
            max_severity = "HIGH"
        elif "MEDIUM" in severities:
            max_severity = "MEDIUM"

        # Determine action
        actions = [v.get("action", "BLOCK_BUY") for v in active]
        if "EXIT_ALL" in actions:
            signal_override = "EXIT ALL POSITIONS"
        elif vetoed:
            signal_override = "STAND ASIDE"
        else:
            signal_override = None

        return {
            "vetoed": vetoed,
            "veto_count": len(active),
            "max_severity": max_severity,
            "signal_override": signal_override,
            "active_vetoes": [
                {
                    "type": v["type"],
                    "reason": v["reason"],
                    "severity": v["severity"],
                    "expires": v.get("expires"),
                }
                for v in active
            ],
        }

    def _create_veto(
        self,
        symbol: str,
        veto_type: str,
        reason: str,
        severity: str = "HIGH",
        duration_days: int = 0,
        action: str = "BLOCK_BUY",
    ) -> Dict[str, Any]:
        """Create a structured veto record."""
        now = datetime.now(IST)
        expires = (now + timedelta(days=duration_days)).isoformat() if duration_days > 0 else None

        return {
            "symbol": symbol,
            "type": veto_type,
            "reason": reason,
            "severity": severity,
            "action": action,
            "triggered_at": now.isoformat(),
            "expires": expires,
            "duration_days": duration_days,
        }

    def get_earnings_suppression_factor(
        self,
        days_to_earnings: int,
    ) -> float:
        """
        Calculate position sizing suppression near earnings.

        From alpha_config.yaml:
        - 5 days before: reduce to 50%
        - 1 day before: exit completely (0%)
        - 2 days after: re-entry allowed

        Returns:
            Float between 0.0 (full block) and 1.0 (no suppression)
        """
        if days_to_earnings <= 1:
            return 0.0    # Exit completely 1 day before
        elif days_to_earnings <= 5:
            return 0.5    # Reduce to 50%
        return 1.0        # No suppression

    def get_active_vetoes_summary(self) -> List[Dict[str, str]]:
        """Get a human-readable summary of currently active vetoes."""
        now = datetime.now(IST)
        active = []

        for v in self.veto_history:
            expires = v.get("expires")
            if expires:
                exp_dt = datetime.fromisoformat(expires)
                if exp_dt.tzinfo is None:
                    exp_dt = IST.localize(exp_dt)
                if exp_dt < now:
                    continue  # Expired
            active.append({
                "symbol": v["symbol"],
                "type": v["type"],
                "reason": v["reason"],
                "severity": v["severity"],
            })

        return active


# ─── Global Singleton ────────────────────────────────────────
veto_engine = VetoEngine()
