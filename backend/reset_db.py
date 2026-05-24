import sqlite3
import os

try:
    import database as db
    
    db.db_execute("DELETE FROM paper_trades")
    db.db_execute("DELETE FROM paper_portfolio")
    db.db_execute("INSERT INTO paper_portfolio (date, cash, holdings_value, total_equity, open_positions, daily_return_pct, cumulative_return_pct, drawdown_from_peak_pct) VALUES (CURRENT_DATE, 1000000, 0, 1000000, 0, 0, 0, 0)")
    print("Database reset successfully.")
except Exception as e:
    print(f"Error resetting database: {e}")
