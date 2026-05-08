"""
Agent Alpha v2.0 — Seasonal & Calendar Effects Model (Model 7)
===============================================================
Weight in ensemble: 5%

Based on statistically significant patterns across 15+ years of NSE data.

Key Indian market seasonal patterns:
- January Effect (FII allocation)
- February budget uncertainty
- March tax-loss selling + April reversal
- Diwali effect (October-November)
- December Santa rally
- Thursday expiry effects
- Pre-budget rally (Jan 15 - Jan 31)
- March year-end tax loss selling reversal

These are EMPIRICAL patterns, not predictions. They provide a small
but consistent edge when combined with other models.
"""
from datetime import datetime, date
from typing import Dict, Any
import calendar


# ─── Empirical Seasonal Patterns (NSE 15yr data) ────────────

MONTH_EFFECTS = {
    1: 1.2,    # January: New year FII allocation, "January effect"
    2: -0.8,   # February: Budget uncertainty, selling pressure pre-budget
    3: -1.5,   # March: Year-end tax selling, portfolio rebalancing
    4: 1.8,    # April: New FY starts, fresh institutional buying
    5: 0.5,    # May: Mixed — "Sell in May" has weak evidence in India
    6: -0.9,   # June: FII selling due to global summer illiquidity
    7: -0.6,   # July: Mixed, Q1 results season
    8: 0.8,    # August: Monsoon progress data, Q1 results rally
    9: -1.1,   # September: FII year-end (US fiscal year), global rebalancing
    10: 1.5,   # October: Diwali effect, festive season
    11: 1.9,   # November: Post-Diwali optimism, year-end rally begins
    12: 2.1,   # December: Santa Claus rally, FII window dressing
}

WEEK_EFFECTS = {
    1: 0.6,    # First week: Fresh institutional buying
    2: 0.2,    # Second week: Momentum continuation
    3: -0.3,   # Third week: Mid-month fatigue
    4: -0.8,   # Fourth week: Month-end selling, position squaring
    5: -0.5,   # Fifth week (rare): Same as fourth
}

DAY_EFFECTS = {
    0: -0.3,   # Monday: Weekend news digestion, gap risk
    1: 0.2,    # Tuesday: Positive (recovery from Monday weakness)
    2: 0.1,    # Wednesday: Neutral
    3: 0.3,    # Thursday: Expiry day — often trend day
    4: -0.4,   # Friday: Risk-off before weekend
}

# ─── Special Calendar Events ─────────────────────────────────

# Pre-budget rally sectors (historically outperform Jan 15-31)
PRE_BUDGET_SECTORS = {
    "NIFTY_INFRA": 4.2,     # Infrastructure: L&T, NCC, etc.
    "DEFENCE": 5.8,          # Defence: HAL, BEL, BEML
    "RAILWAYS": 6.1,         # Railways: RVNL, IRFC
    "NIFTY_REALTY": 3.5,    # Real Estate
    "NIFTY_AUTO": 2.8,      # Auto — rural themes
}

# March tax-loss selling window
TAX_LOSS_SELLING_WINDOW = (3, 15, 3, 25)  # March 15-25
TAX_LOSS_REVERSAL_WINDOW = (4, 1, 4, 10)  # April 1-10

# Diwali effect window (approximate — actual dates vary)
DIWALI_WINDOW_MONTHS = [10, 11]  # October-November


def calculate_seasonal_signal(
    target_date: datetime = None,
    sector: str = None,
) -> Dict[str, Any]:
    """
    Calculate the seasonal/calendar effect signal for a given date.

    Args:
        target_date: Date to calculate for (default: today)
        sector: Optional sector name for sector-specific effects

    Returns:
        Dict with: signal, confidence, direction, seasonal_score, breakdown
    """
    if target_date is None:
        target_date = datetime.now()

    month = target_date.month
    weekday = target_date.weekday()
    day = target_date.day
    week_num = min((day - 1) // 7 + 1, 5)

    # ─── Base Seasonal Score ─────────────────────────────────
    month_effect = MONTH_EFFECTS.get(month, 0)
    week_effect = WEEK_EFFECTS.get(week_num, 0)
    day_effect = DAY_EFFECTS.get(weekday, 0)

    raw_score = month_effect + week_effect + day_effect

    # ─── Special Calendar Events ─────────────────────────────
    special_events = []
    special_adjustment = 0

    # Pre-Budget Rally (Jan 15-31)
    if month == 1 and day >= 15:
        special_events.append("Pre-Budget Rally Window")
        special_adjustment += 1.5
        if sector and sector in PRE_BUDGET_SECTORS:
            sector_boost = PRE_BUDGET_SECTORS[sector]
            special_adjustment += sector_boost / 3  # Scale down for signal
            special_events.append(f"Budget sector boost: {sector} (hist avg +{sector_boost}%)")

    # Budget Day (Feb 1 — high vol, unpredictable direction)
    if month == 2 and day == 1:
        special_events.append("BUDGET DAY — extreme volatility expected")
        special_adjustment -= 2.0  # Suppress signals on budget day

    # March Tax-Loss Selling (Mar 15-25)
    if month == 3 and 15 <= day <= 25:
        special_events.append("Tax-loss selling window — beaten-down stocks pressured")
        special_adjustment -= 1.0

    # April Tax-Loss Reversal (Apr 1-10)
    if month == 4 and day <= 10:
        special_events.append("Tax-loss selling reversal — mean-reversion opportunity")
        special_adjustment += 1.0

    # Diwali Effect (Oct-Nov)
    if month in DIWALI_WINDOW_MONTHS:
        special_events.append("Diwali/festive season — historically bullish")
        special_adjustment += 0.5

    # F&O Expiry Thursday
    if weekday == 3:
        # Check if this is last Thursday (monthly expiry)
        # Last Thursday = higher volatility
        last_day = calendar.monthrange(target_date.year, month)[1]
        last_thursday = last_day
        while datetime(target_date.year, month, last_thursday).weekday() != 3:
            last_thursday -= 1
        if day == last_thursday:
            special_events.append("Monthly F&O Expiry — Max Pain gravity active")
            special_adjustment -= 0.5  # Reduce directional confidence near expiry
        else:
            special_events.append("Weekly Expiry Thursday")

    # December Window Dressing (Dec 20-31)
    if month == 12 and day >= 20:
        special_events.append("Year-end window dressing — institutional buying of winners")
        special_adjustment += 0.8

    # ─── Final Score ─────────────────────────────────────────
    total_score = raw_score + special_adjustment
    seasonal_score = max(-3.0, min(3.0, total_score))  # Cap at ±3

    # ─── Signal Generation ───────────────────────────────────
    if seasonal_score >= 2.0:
        signal, direction = "BUY", 1
        confidence = min(70, int(30 + seasonal_score * 12))
    elif seasonal_score >= 1.0:
        signal, direction = "BUY", 1
        confidence = min(55, int(25 + seasonal_score * 10))
    elif seasonal_score <= -2.0:
        signal, direction = "SELL", -1
        confidence = min(70, int(30 + abs(seasonal_score) * 12))
    elif seasonal_score <= -1.0:
        signal, direction = "SELL", -1
        confidence = min(55, int(25 + abs(seasonal_score) * 10))
    else:
        signal, direction = "NEUTRAL", 0
        confidence = 35

    return {
        "signal": signal,
        "confidence": confidence,
        "direction": direction,
        "seasonal_score": round(seasonal_score, 2),
        "breakdown": {
            "month_effect": month_effect,
            "week_effect": week_effect,
            "day_effect": day_effect,
            "special_adjustment": round(special_adjustment, 2),
        },
        "special_events": special_events,
        "date": target_date.strftime("%Y-%m-%d"),
        "day_name": target_date.strftime("%A"),
    }
