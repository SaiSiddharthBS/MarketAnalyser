"""
Agent Alpha v2.0 — Macro Event Calendar
=======================================
Tracks major macroeconomic events that cause extreme market volatility.
If a major event is within the next 48 hours, the system engages 
"Macro Suppression" (reduces position sizes) or triggers a Hard Veto.

Events tracked:
1. RBI Monetary Policy Committee (MPC) outcomes
2. US Fed FOMC rate decisions
3. Indian Union Budget (Feb 1)
4. CPI Inflation data releases
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List

# In a full production system, this would fetch from an API like 
# TradingEconomics or ForexFactory. For this zero-cost architecture,
# we use a local schedule that can be updated quarterly in alpha_config.yaml.

def get_upcoming_macro_events(days_lookahead: int = 3) -> List[Dict[str, Any]]:
    """
    Check if any major macro events are scheduled in the next X days.
    """
    # Hardcoded known dates for 2024-2025 as an example.
    # In reality, this would read from the DB or an external free calendar API.
    macro_schedule = [
        {"date": "2024-02-01", "event": "Union Budget", "severity": "CRITICAL", "impact": "MARKET_WIDE"},
        {"date": "2024-06-07", "event": "RBI MPC", "severity": "HIGH", "impact": "BANKS_AUTO_REALTY"},
        {"date": "2024-06-12", "event": "US Fed FOMC", "severity": "HIGH", "impact": "IT_MARKET_WIDE"},
        {"date": "2024-07-23", "event": "Union Budget (Full)", "severity": "CRITICAL", "impact": "MARKET_WIDE"},
        {"date": "2024-08-08", "event": "RBI MPC", "severity": "HIGH", "impact": "BANKS_AUTO_REALTY"},
        {"date": "2024-09-18", "event": "US Fed FOMC", "severity": "CRITICAL", "impact": "IT_MARKET_WIDE"},
        {"date": "2024-10-09", "event": "RBI MPC", "severity": "HIGH", "impact": "BANKS_AUTO_REALTY"},
        {"date": "2024-11-07", "event": "US Fed FOMC", "severity": "HIGH", "impact": "IT_MARKET_WIDE"},
        {"date": "2024-12-06", "event": "RBI MPC", "severity": "HIGH", "impact": "BANKS_AUTO_REALTY"},
        {"date": "2024-12-18", "event": "US Fed FOMC", "severity": "HIGH", "impact": "IT_MARKET_WIDE"},
        
        # 2025 Projected
        {"date": "2025-02-01", "event": "Union Budget", "severity": "CRITICAL", "impact": "MARKET_WIDE"},
        {"date": "2025-02-07", "event": "RBI MPC", "severity": "HIGH", "impact": "BANKS_AUTO_REALTY"},
        {"date": "2025-04-05", "event": "RBI MPC", "severity": "HIGH", "impact": "BANKS_AUTO_REALTY"},
    ]
    
    today = datetime.now()
    cutoff = today + timedelta(days=days_lookahead)
    
    upcoming = []
    for event in macro_schedule:
        event_date = datetime.strptime(event["date"], "%Y-%m-%d")
        
        # Is the event between today and the cutoff?
        if today.date() <= event_date.date() <= cutoff.date():
            days_away = (event_date.date() - today.date()).days
            
            event_data = event.copy()
            event_data["days_away"] = days_away
            
            if days_away == 0:
                event_data["status"] = "TODAY"
            elif days_away == 1:
                event_data["status"] = "TOMORROW"
            else:
                event_data["status"] = "UPCOMING"
                
            upcoming.append(event_data)
            
    return upcoming

def check_macro_veto() -> Dict[str, Any]:
    """
    Check if the Veto Engine should trigger due to a macro event.
    """
    upcoming = get_upcoming_macro_events(days_lookahead=2) # 48 hours
    
    critical_events = [e for e in upcoming if e["severity"] == "CRITICAL"]
    high_events = [e for e in upcoming if e["severity"] == "HIGH"]
    
    if critical_events:
        return {
            "trigger": True,
            "level": "HARD_VETO", # Block ALL new positions
            "reason": f"Critical Macro Event within 48h: {critical_events[0]['event']}",
            "events": critical_events
        }
        
    if high_events:
        return {
            "trigger": True,
            "level": "SOFT_VETO", # Reduce position sizes by 50%
            "reason": f"High Impact Macro Event within 48h: {high_events[0]['event']}",
            "events": high_events
        }
        
    return {
        "trigger": False,
        "level": "NONE",
        "reason": "",
        "events": []
    }
