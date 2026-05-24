import database as db
trades = db.db_execute("SELECT symbol, status, entry_price FROM paper_trades WHERE status = 'OPEN'")
print("Open Trades:", trades)
