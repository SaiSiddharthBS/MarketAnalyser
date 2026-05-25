import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import db_execute

try:
    print("Checking database tables...")
    tables = db_execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    for t in tables:
        name = t['table_name']
        count = db_execute(f"SELECT COUNT(*) as count FROM {name}")
        c = count[0]['count'] if count else 0
        print(f"Table: {name} | Rows: {c}")
except Exception as e:
    print("Database error:", e)
