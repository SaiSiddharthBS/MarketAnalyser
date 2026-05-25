def run():
    trade_type = "PAIR_LONG"
    exit_reason = None
    if trade_type.startswith("PAIR_"):
        pass
    elif trade_type in ("LONG", "SHORT"):
        pass
        
    # Wait, what about lines 202+?
    expected_days = 5
    max_hold_limit = 7
    days_held = 10
    if not exit_reason and days_held >= max_hold_limit:
        exit_reason = f"TIMEOUT_{max_hold_limit}D"
        
    return exit_reason
print(run())
