"""
MarketPulse — Mutual Fund Data Fetcher
Uses mftool + MFAPI.in for Indian mutual fund data.
"""
import requests
from datetime import datetime
import ssl

# Fix Mac SSL issue
ssl._create_default_https_context = ssl._create_unverified_context

MFAPI_BASE = "https://api.mfapi.in/mf"


def get_mf_nav(scheme_code):
    """Get latest NAV for a mutual fund scheme."""
    try:
        resp = requests.get(f"{MFAPI_BASE}/{scheme_code}/latest", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("data"):
                nav_data = data["data"][0]
                return {
                    "scheme_code": scheme_code,
                    "scheme_name": data.get("meta", {}).get("scheme_name", ""),
                    "nav": float(nav_data.get("nav", 0)),
                    "date": nav_data.get("date", ""),
                    "category": data.get("meta", {}).get("scheme_category", ""),
                    "fund_house": data.get("meta", {}).get("fund_house", ""),
                }
    except Exception as e:
        print(f"Error fetching NAV for {scheme_code}: {e}")
    return None


def get_mf_historical(scheme_code, days=365):
    """Get historical NAV data for a scheme."""
    try:
        resp = requests.get(f"{MFAPI_BASE}/{scheme_code}", timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            nav_list = data.get("data", [])[:days]
            result = []
            for item in nav_list:
                try:
                    result.append({
                        "date": item["date"],
                        "nav": float(item["nav"]),
                    })
                except (ValueError, KeyError):
                    continue
            return {
                "scheme_code": scheme_code,
                "scheme_name": data.get("meta", {}).get("scheme_name", ""),
                "category": data.get("meta", {}).get("scheme_category", ""),
                "fund_house": data.get("meta", {}).get("fund_house", ""),
                "nav_history": result,
            }
    except Exception as e:
        print(f"Error fetching history for {scheme_code}: {e}")
    return None


def calculate_mf_returns(nav_history):
    """Calculate returns for various periods from NAV history."""
    if not nav_history or len(nav_history) < 2:
        return {}

    current_nav = nav_history[0]["nav"]
    returns = {}

    period_map = {"1W": 5, "1M": 22, "3M": 66, "6M": 132, "1Y": 252, "3Y": 756, "5Y": 1260}
    for label, days in period_map.items():
        if len(nav_history) > days:
            old_nav = nav_history[days]["nav"]
            if old_nav > 0:
                ret = ((current_nav - old_nav) / old_nav) * 100
                returns[label] = round(ret, 2)
    return returns


def get_mf_portfolio_value(holdings):
    """
    Calculate current value for a list of MF holdings.
    holdings: list of dicts with scheme_code, invested, units (optional)
    """
    results = []
    total_invested = 0
    total_current = 0

    for h in holdings:
        nav_data = get_mf_nav(h["scheme_code"])
        if not nav_data:
            continue

        current_nav = nav_data["nav"]
        invested = h["invested"]

        # If units not provided, estimate from invested amount and current NAV
        units = h.get("units")
        if not units and invested and current_nav:
            # This is an approximation — ideally units come from actual purchase
            units = invested / current_nav

        current_value = units * current_nav if units else invested
        returns_pct = ((current_value - invested) / invested) * 100 if invested else 0

        results.append({
            "scheme_code": h["scheme_code"],
            "scheme_name": nav_data.get("scheme_name", ""),
            "category": nav_data.get("category", ""),
            "invested": invested,
            "current_value": round(current_value, 2),
            "nav": current_nav,
            "units": round(units, 4) if units else None,
            "returns": round(returns_pct, 2),
            "returns_abs": round(current_value - invested, 2),
        })
        total_invested += invested
        total_current += current_value

    return {
        "holdings": results,
        "total_invested": total_invested,
        "total_current": round(total_current, 2),
        "total_returns": round(total_current - total_invested, 2),
        "total_returns_pct": round(((total_current - total_invested) / total_invested) * 100, 2) if total_invested else 0,
    }


def search_mf(query):
    """Search mutual funds by name."""
    try:
        resp = requests.get(f"{MFAPI_BASE}/search?q={query}", timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return []
