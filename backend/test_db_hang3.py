import database as db
import sys

print("Testing init_db with prints...")
def patched_init_db():
    conn = db.get_connection()
    cursor = db.get_cursor(conn)
    
    print("Got connection and cursor.")
    # just create one table to test
    cursor.execute("CREATE TABLE IF NOT EXISTS test_table (id serial primary key, name text);")
    conn.commit()
    print("Committed table creation.")
    db.put_connection(conn)
    print("Returned connection.")
    
    print("Starting migration...")
    m_conn = db.get_connection()
    m_cur = db.get_cursor(m_conn)
    try:
        print("Executing ALTER...")
        m_cur.execute("ALTER TABLE test_table ADD COLUMN test_col text;")
        m_conn.commit()
        print("Committed ALTER.")
    except Exception as e:
        print(f"Failed ALTER: {e}")
        m_conn.rollback()
    finally:
        m_cur.close()
        db.put_connection(m_conn)
    print("All done!")

patched_init_db()
