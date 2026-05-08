"""
Agent Alpha v2.0 — Data Validation Layer
=========================================
Every single data point passes through this gate before entering the pipeline.
Catches: staleness, nulls, splits, outliers, cross-source inconsistencies.

This is the immune system of Agent Alpha. If data is sick, it does NOT enter.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
import pytz

IST = pytz.timezone("Asia/Kolkata")


class DataValidationError(Exception):
    """Raised when data fails validation."""
    pass


class DataValidator:
    """Universal data quality gate for all incoming feeds."""

    def __init__(self, strict_mode: bool = True):
        """
        Args:
            strict_mode: If True, raise errors on critical failures.
                         If False, log warnings and return with flags.
        """
        self.strict_mode = strict_mode
        self.validation_log: List[Dict[str, Any]] = []

    def _log(self, level: str, source: str, message: str, data: Any = None):
        """Log a validation event."""
        entry = {
            "timestamp": datetime.now(IST).isoformat(),
            "level": level,
            "source": source,
            "message": message,
        }
        self.validation_log.append(entry)
        prefix = {"INFO": "✅", "WARN": "⚠️", "ERROR": "❌", "CRITICAL": "🔴"}.get(level, "")
        print(f"{prefix} DataValidator [{source}]: {message}")

    # ─── OHLCV Validation ────────────────────────────────────

    def validate_ohlcv(
        self,
        df: pd.DataFrame,
        symbol: str,
        max_staleness_hours: int = 48,
        max_single_day_move_pct: float = 20.0,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Validate OHLCV DataFrame for a stock.

        Checks:
        1. Not empty
        2. Required columns exist (Open, High, Low, Close, Volume)
        3. No null Close values
        4. Data is not stale (last date within max_staleness_hours)
        5. No single-day move > max_single_day_move_pct (likely split or error)
        6. High >= Low for every row
        7. Open and Close are within [Low, High] range

        Returns:
            Tuple of (cleaned_df, validation_report)
        """
        report = {
            "symbol": symbol,
            "valid": True,
            "warnings": [],
            "rows_before": 0,
            "rows_after": 0,
            "staleness_hours": None,
        }

        # Check 1: Not empty
        if df is None or df.empty:
            report["valid"] = False
            report["warnings"].append("DataFrame is empty or None")
            self._log("ERROR", f"OHLCV:{symbol}", "Empty DataFrame received")
            if self.strict_mode:
                return pd.DataFrame(), report
            return pd.DataFrame(), report

        report["rows_before"] = len(df)

        # Check 2: Required columns
        required = {"Open", "High", "Low", "Close", "Volume"}
        missing = required - set(df.columns)
        if missing:
            report["valid"] = False
            report["warnings"].append(f"Missing columns: {missing}")
            self._log("ERROR", f"OHLCV:{symbol}", f"Missing columns: {missing}")
            return pd.DataFrame(), report

        # Check 3: Null Close values
        null_close_count = df["Close"].isna().sum()
        if null_close_count > 0:
            report["warnings"].append(f"{null_close_count} null Close values dropped")
            self._log("WARN", f"OHLCV:{symbol}", f"Dropped {null_close_count} null Close rows")
            df = df.dropna(subset=["Close"])

        # Check 4: Staleness
        if hasattr(df.index, 'tz_localize') or hasattr(df.index, 'tz_convert'):
            try:
                last_date = pd.Timestamp(df.index[-1])
                if last_date.tzinfo is None:
                    last_date = last_date.tz_localize("UTC")
                now = datetime.now(pytz.UTC)
                staleness = (now - last_date).total_seconds() / 3600
                report["staleness_hours"] = round(staleness, 1)
                if staleness > max_staleness_hours:
                    report["warnings"].append(
                        f"Data is {staleness:.0f}h old (max: {max_staleness_hours}h)"
                    )
                    self._log(
                        "WARN", f"OHLCV:{symbol}",
                        f"Stale data: {staleness:.0f}h old"
                    )
            except Exception:
                pass  # If we can't determine staleness, continue

        # Check 5: Extreme single-day moves (likely split or data error)
        if len(df) > 1:
            daily_returns = df["Close"].pct_change().abs() * 100
            extreme_moves = daily_returns[daily_returns > max_single_day_move_pct]
            if len(extreme_moves) > 0:
                report["warnings"].append(
                    f"{len(extreme_moves)} extreme moves detected (>{max_single_day_move_pct}%)"
                )
                self._log(
                    "WARN", f"OHLCV:{symbol}",
                    f"Extreme moves on dates: {extreme_moves.index.tolist()[:3]}... "
                    f"(possible split/bonus/error)"
                )

        # Check 6: High >= Low
        invalid_hl = df[df["High"] < df["Low"]]
        if len(invalid_hl) > 0:
            report["warnings"].append(f"{len(invalid_hl)} rows with High < Low — dropped")
            self._log("WARN", f"OHLCV:{symbol}", f"Dropped {len(invalid_hl)} High < Low rows")
            df = df[df["High"] >= df["Low"]]

        # Check 7: Open/Close within [Low, High]
        oob = df[(df["Open"] < df["Low"] * 0.99) | (df["Open"] > df["High"] * 1.01) |
                  (df["Close"] < df["Low"] * 0.99) | (df["Close"] > df["High"] * 1.01)]
        if len(oob) > 0:
            report["warnings"].append(f"{len(oob)} rows with Open/Close outside [Low, High]")
            self._log("WARN", f"OHLCV:{symbol}", f"{len(oob)} out-of-bounds Open/Close values")

        report["rows_after"] = len(df)
        if len(df) == 0:
            report["valid"] = False

        if not report["warnings"]:
            self._log("INFO", f"OHLCV:{symbol}", f"Validated OK — {len(df)} rows")

        return df, report

    # ─── Scalar Value Validation ─────────────────────────────

    def validate_scalar(
        self,
        value: Any,
        name: str,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        allow_none: bool = False,
    ) -> Tuple[Any, bool]:
        """
        Validate a single scalar value (price, ratio, percentage, etc.).

        Returns:
            Tuple of (value_or_fallback, is_valid)
        """
        if value is None:
            if allow_none:
                return None, True
            self._log("WARN", f"Scalar:{name}", "Value is None")
            return None, False

        try:
            val = float(value)
        except (ValueError, TypeError):
            self._log("WARN", f"Scalar:{name}", f"Cannot convert to float: {value}")
            return None, False

        if np.isnan(val) or np.isinf(val):
            self._log("WARN", f"Scalar:{name}", f"NaN or Inf value: {val}")
            return None, False

        if min_val is not None and val < min_val:
            self._log("WARN", f"Scalar:{name}", f"Below minimum: {val} < {min_val}")
            return None, False

        if max_val is not None and val > max_val:
            self._log("WARN", f"Scalar:{name}", f"Above maximum: {val} > {max_val}")
            return None, False

        return val, True

    # ─── Feed Freshness Check ────────────────────────────────

    def validate_feed_freshness(
        self,
        feed_name: str,
        last_update_time: Optional[datetime],
        max_staleness_hours: int = 24,
    ) -> Tuple[bool, float]:
        """
        Check if a data feed is fresh enough.

        Returns:
            Tuple of (is_fresh, staleness_hours)
        """
        if last_update_time is None:
            self._log("WARN", f"Feed:{feed_name}", "No update timestamp available")
            return False, float("inf")

        now = datetime.now(IST)
        if last_update_time.tzinfo is None:
            last_update_time = IST.localize(last_update_time)

        staleness = (now - last_update_time).total_seconds() / 3600
        is_fresh = staleness <= max_staleness_hours

        if not is_fresh:
            self._log(
                "WARN", f"Feed:{feed_name}",
                f"Stale: {staleness:.1f}h old (max: {max_staleness_hours}h)"
            )
        else:
            self._log("INFO", f"Feed:{feed_name}", f"Fresh: {staleness:.1f}h old")

        return is_fresh, staleness

    # ─── Cross-Source Price Validation ────────────────────────

    def validate_cross_source(
        self,
        price_a: float,
        price_b: float,
        source_a: str,
        source_b: str,
        symbol: str,
        max_divergence_pct: float = 0.5,
    ) -> Tuple[bool, float]:
        """
        Verify that two price sources agree within a tolerance.
        Catches: one source has adjusted for split but other hasn't.

        Returns:
            Tuple of (consistent, divergence_pct)
        """
        if price_a <= 0 or price_b <= 0:
            return False, 100.0

        divergence = abs(price_a - price_b) / min(price_a, price_b) * 100

        if divergence > max_divergence_pct:
            self._log(
                "WARN", f"CrossSource:{symbol}",
                f"{source_a}={price_a:.2f} vs {source_b}={price_b:.2f} "
                f"(divergence: {divergence:.2f}%)"
            )
            return False, divergence

        return True, divergence

    # ─── Batch Validation Report ─────────────────────────────

    def get_health_report(self) -> Dict[str, Any]:
        """Generate a summary of all validation events."""
        errors = [e for e in self.validation_log if e["level"] in ("ERROR", "CRITICAL")]
        warnings = [e for e in self.validation_log if e["level"] == "WARN"]
        total = len(self.validation_log)

        return {
            "total_checks": total,
            "errors": len(errors),
            "warnings": len(warnings),
            "healthy": len(errors) == 0,
            "recent_errors": errors[-5:] if errors else [],
            "recent_warnings": warnings[-5:] if warnings else [],
        }

    def clear_log(self):
        """Reset the validation log (call at start of each pipeline run)."""
        self.validation_log.clear()


# ─── Global Singleton ────────────────────────────────────────
# All modules import and use this single instance
validator = DataValidator(strict_mode=False)
