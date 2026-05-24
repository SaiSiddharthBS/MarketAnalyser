import database as db

def test():
    conn = db.get_connection()
    conn.autocommit = True
    cursor = db.get_cursor(conn)
    cursor.execute("CREATE TABLE IF NOT EXISTS test_table2 (id serial primary key, name text);")
    db.put_connection(conn)
    
    m_conn = db.get_connection()
    m_conn.autocommit = True
    m_cur = db.get_cursor(m_conn)
    try:
        print("Executing ALTER...")
        m_cur.execute("ALTER TABLE test_table2 ADD COLUMN test_col text;")
        print("ALTER done")
    except Exception as e:
        print(f"Failed ALTER: {e}")
    finally:
        m_cur.close()
        db.put_connection(m_conn)
    print("Done!")

test()
