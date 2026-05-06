"""
MarketPulse — Position Sizing Engine
Calculates optimal position size based on risk management rules.

Formula: Position Size (shares) = (Capital × Risk% per trade) / (Entry − Stop Loss)
"""


def calculate_position(entry_price, stop_loss, capital=500000, risk_pct=1.0, max_position_pct=25.0):
    """Calculate position size for a trade.

    Args:
        entry_price: Entry price per share (₹)
        stop_loss: Stop loss price per share (₹)
        capital: Total trading capital (₹)
        risk_pct: Max risk per trade as % of capital (default 1%)
        max_position_pct: Max single position as % of capital (default 25%)

    Returns:
        Dictionary with quantity, deployed capital, max loss, etc.
    """
    if entry_price <= 0 or stop_loss <= 0 or entry_price <= stop_loss:
        return {
            "quantity": 0,
            "capital_deployed": 0,
            "max_loss": 0,
            "error": "Invalid entry/stop loss prices",
        }

    risk_per_share = entry_price - stop_loss
    risk_amount = capital * (risk_pct / 100)
    max_position_value = capital * (max_position_pct / 100)

    # Calculate quantity based on risk
    quantity = int(risk_amount / risk_per_share)

    # Cap by max position size
    max_qty_by_position = int(max_position_value / entry_price)
    quantity = min(quantity, max_qty_by_position)

    # Ensure at least 1 share
    quantity = max(1, quantity)

    capital_deployed = round(quantity * entry_price, 2)
    max_loss = round(quantity * risk_per_share, 2)
    capital_pct = round((capital_deployed / capital) * 100, 2) if capital > 0 else 0

    return {
        "quantity": quantity,
        "capital_deployed": capital_deployed,
        "capital_pct": capital_pct,
        "max_loss": max_loss,
        "risk_per_share": round(risk_per_share, 2),
        "risk_amount_allowed": round(risk_amount, 2),
    }


def check_portfolio_exposure(positions, capital=500000):
    """Check portfolio concentration and generate warnings.

    Args:
        positions: List of dicts with 'symbol', 'sector', 'value'
        capital: Total capital

    Returns:
        Dictionary with sector breakdown and warnings.
    """
    if not positions:
        return {"sectors": {}, "warnings": []}

    sector_totals = {}
    stock_pcts = {}
    warnings = []

    for p in positions:
        sector = p.get("sector", "Unknown")
        value = p.get("value", 0)
        symbol = p.get("symbol", "")

        sector_totals[sector] = sector_totals.get(sector, 0) + value
        stock_pcts[symbol] = round((value / capital) * 100, 2) if capital > 0 else 0

    # Calculate sector percentages
    sectors = {}
    for sector, total in sector_totals.items():
        pct = round((total / capital) * 100, 2) if capital > 0 else 0
        sectors[sector] = {"value": round(total, 2), "pct": pct}

        if pct > 40:
            warnings.append(f"⚠️ High sector concentration: {sector} at {pct}%")
        elif pct > 30:
            warnings.append(f"🟡 Elevated sector exposure: {sector} at {pct}%")

    # Check individual stock concentration
    for symbol, pct in stock_pcts.items():
        if pct > 25:
            warnings.append(f"⚠️ Oversized position: {symbol} at {pct}%")

    return {"sectors": sectors, "warnings": warnings}
