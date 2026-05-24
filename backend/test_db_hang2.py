import database as db

print("Starting migration test...")
m_conn = db.get_connection()
print("Got connection for migration 1")
try:
    m_cur = db.get_cursor(m_conn)
    print("Got cursor")
    print("Executing ALTER TABLE...")
    m_cur.execute("ALTER TABLE daily_predictions ADD COLUMN pred_support REAL")
    print("Execute done")
    m_conn.commit()
    print("Commit done")
    m_cur.close()
    print("Cursor closed")
except Exception as e:
    print(f"Failed: {e}")
    m_conn.rollback()
finally:
    db.put_connection(m_conn)
    print("Connection returned")
print("Done")
