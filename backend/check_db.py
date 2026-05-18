import sys
import os
sys.path.append(os.path.dirname(__file__))
import database as db
res = db.db_execute("SELECT * FROM paper_trades LIMIT 1")
print(res)
if not res:
    if db.pool:
        print(db.db_execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'paper_trades'"))
    else:
        print(db.db_execute("PRAGMA table_info(paper_trades)"))
