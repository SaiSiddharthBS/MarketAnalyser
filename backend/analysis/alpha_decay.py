"""
Agent Alpha v2.0 — Alpha Decay Monitor
========================================
Every signal's edge has a half-life. This monitor detects when edges
are dying before they destroy your P&L.

A signal that was 70% accurate last quarter may be 55% accurate this
quarter because:
- The market regime changed
- Other participants discovered the same signal (crowding)
- Structural market changes (regulation, new instruments)

This module tracks rolling accuracy per model and automatically:
- Downweights signals whose accuracy drops > 8% from baseline
- Suspends signals whose accuracy drops > 15% from baseline
- Alerts when systemic decay is detected across multiple models
"""
import numpy as np
from collections import deque
from datetime import datetime
from typing import Dict, Any, List, Optional


class AlphaDecayMonitor:
    """
    Monitors the rolling accuracy of each signal model and detects decay.
    
    Usage:
        monitor = AlphaDecayMonitor(["momentum", "order_flow", ...])
        
        # After each prediction resolves:
        monitor.update("momentum", prediction=1, actual=1)  # Correct
        monitor.update("momentum", prediction=1, actual=-1) # Wrong
        
        # Check for decay:
        report = monitor.get_decay_report()
    """

    def __init__(
        self,
        signal_names: List[str],
        lookback: int = 60,
        decay_threshold: float = 0.08,
        suspend_threshold: float = 0.15,
    ):
        """
        Args:
            signal_names: List of model names to monitor
            lookback: Rolling window size in trading days (default 60)
            decay_threshold: Absolute accuracy drop to trigger downweight (default 8%)
            suspend_threshold: Absolute accuracy drop to suspend signal (default 15%)
        """
        self.signal_names = signal_names
        self.lookback = lookback
        self.decay_threshold = decay_threshold
        self.suspend_threshold = suspend_threshold

        # Rolling accuracy windows per signal
        self.rolling_results: Dict[str, deque] = {
            name: deque(maxlen=lookback) for name in signal_names
        }

        # Baseline accuracy (set during initial backtest or first N predictions)
        self.baseline_accuracy: Dict[str, float] = {}

        # Track when baselines were set
        self.baseline_set_at: Dict[str, str] = {}

        # Minimum predictions before decay detection activates
        self.min_predictions = 30

    def set_baseline(self, signal_name: str, accuracy: float):
        """
        Set the baseline accuracy for a signal (from initial backtest).
        
        Args:
            signal_name: Model name
            accuracy: Baseline accuracy (e.g., 0.65 = 65%)
        """
        self.baseline_accuracy[signal_name] = accuracy
        self.baseline_set_at[signal_name] = datetime.now().isoformat()

    def update(self, signal_name: str, prediction: int, actual: int):
        """
        Record a prediction outcome.

        Args:
            signal_name: Model name
            prediction: Predicted direction (1=BUY, -1=SELL, 0=NEUTRAL)
            actual: Actual outcome (1=up, -1=down, 0=flat)
        """
        if signal_name not in self.rolling_results:
            self.rolling_results[signal_name] = deque(maxlen=self.lookback)

        # 1 if prediction matched actual direction, 0 otherwise
        correct = 1 if prediction == actual else 0
        self.rolling_results[signal_name].append(correct)

    def get_rolling_accuracy(self, signal_name: str) -> Optional[float]:
        """Get current rolling accuracy for a signal."""
        results = self.rolling_results.get(signal_name)
        if not results or len(results) < self.min_predictions:
            return None
        return float(np.mean(list(results)))

    def get_decay_report(self) -> Dict[str, Dict[str, Any]]:
        """
        Generate the alpha decay report for all signals.

        Returns:
            Dict mapping signal_name → decay info:
                - rolling_accuracy: current rolling accuracy
                - baseline_accuracy: original baseline
                - decay_amount: how much accuracy has dropped
                - severity: 0 (healthy) to 1.0 (suspended)
                - status: HEALTHY / DECAYING / SUSPENDED
                - action: what the ensemble should do
        """
        report = {}

        for name in self.signal_names:
            rolling_acc = self.get_rolling_accuracy(name)
            baseline_acc = self.baseline_accuracy.get(name)

            if rolling_acc is None:
                report[name] = {
                    "rolling_accuracy": None,
                    "status": "INSUFFICIENT_DATA",
                    "severity": 0,
                    "action": "Keep monitoring — need more data",
                    "predictions_count": len(self.rolling_results.get(name, [])),
                    "min_required": self.min_predictions,
                }
                continue

            if baseline_acc is None:
                # Auto-set baseline from first complete window
                self.set_baseline(name, rolling_acc)
                baseline_acc = rolling_acc

            decay_amount = baseline_acc - rolling_acc

            if decay_amount > self.suspend_threshold:
                status = "SUSPENDED"
                severity = decay_amount
                action = f"SUSPEND signal — accuracy dropped {decay_amount:.1%} below baseline"
            elif decay_amount > self.decay_threshold:
                status = "DECAYING"
                severity = decay_amount
                reduction_pct = (decay_amount / self.suspend_threshold) * 100
                action = f"DOWNWEIGHT by {reduction_pct:.0f}% — accuracy dropping"
            else:
                status = "HEALTHY"
                severity = 0
                action = "No action needed"

            report[name] = {
                "rolling_accuracy": round(rolling_acc, 4),
                "baseline_accuracy": round(baseline_acc, 4),
                "decay_amount": round(decay_amount, 4),
                "severity": round(severity, 4),
                "status": status,
                "action": action,
                "predictions_count": len(self.rolling_results.get(name, [])),
            }

        return report

    def get_system_health(self) -> Dict[str, Any]:
        """
        Overall system health assessment.

        Returns:
            Dict with: healthy_models, decaying_models, suspended_models,
                        system_status, recommendation
        """
        report = self.get_decay_report()

        healthy = [n for n, r in report.items() if r["status"] == "HEALTHY"]
        decaying = [n for n, r in report.items() if r["status"] == "DECAYING"]
        suspended = [n for n, r in report.items() if r["status"] == "SUSPENDED"]
        insufficient = [n for n, r in report.items() if r["status"] == "INSUFFICIENT_DATA"]

        active_models = len(healthy) + len(decaying)
        total_models = len(self.signal_names)

        if len(suspended) >= 3:
            system_status = "CRITICAL"
            recommendation = "3+ models suspended — system reliability severely degraded. Consider halting trading."
        elif len(suspended) >= 2 or len(decaying) >= 4:
            system_status = "WARNING"
            recommendation = "Multiple model decay detected — reduce overall position sizing by 40%"
        elif len(decaying) >= 2:
            system_status = "CAUTION"
            recommendation = "Some model decay — monitor closely, reduce sizing by 20%"
        else:
            system_status = "HEALTHY"
            recommendation = "All systems nominal"

        return {
            "system_status": system_status,
            "healthy_models": healthy,
            "decaying_models": decaying,
            "suspended_models": suspended,
            "insufficient_data": insufficient,
            "active_model_count": active_models,
            "total_model_count": total_models,
            "recommendation": recommendation,
        }
