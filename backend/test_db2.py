import sqlite3
conn = sqlite3.connect("marketpulse.db")
c = conn.cursor()
c.execute("SELECT symbol, trade_type FROM paper_trades WHERE status = 'OPEN'")
print(c.fetchall())
