import os
from dotenv import load_dotenv
load_dotenv() # Load from .env

import database as db

print("DATABASE_URL IS:", os.getenv("DATABASE_URL"))

db.db_execute("DELETE FROM paper_trades")
db.db_execute("DELETE FROM paper_portfolio")
db.db_execute("INSERT INTO paper_portfolio (date, cash, holdings_value, total_equity, open_positions, daily_return_pct, cumulative_return_pct, drawdown_from_peak_pct) VALUES (CURRENT_DATE, 1000000, 0, 1000000, 0, 0, 0, 0)")
print("Database reset successfully with .env loaded.")
