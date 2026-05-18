import sys
import os
sys.path.append(os.path.dirname(__file__))
import database as db
db.db_execute("DROP TABLE IF EXISTS paper_trades CASCADE")
db.db_execute("DROP TABLE IF EXISTS paper_portfolio CASCADE")
print("Dropped old tables.")
