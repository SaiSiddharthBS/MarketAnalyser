import database as db
conn = db.get_connection()
cur = db.get_cursor(conn)
cur.execute("""
    SELECT pg_terminate_backend(pid) 
    FROM pg_stat_activity 
    WHERE datname = current_database() 
      AND pid <> pg_backend_pid()
      AND state in ('idle in transaction', 'active');
""")
conn.commit()
db.put_connection(conn)
print("Killed other transactions.")
