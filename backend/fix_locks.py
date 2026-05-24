import database as db

conn = db.get_connection()
cursor = db.get_cursor(conn)

print("Checking active locks...")
query = """
SELECT pid, 
       usename, 
       pg_blocking_pids(pid) as blocked_by, 
       query,
       state,
       wait_event_type,
       wait_event
FROM pg_stat_activity 
WHERE pg_backend_pid() <> pid;
"""
cursor.execute(query)
rows = cursor.fetchall()

pids_to_kill = []
for r in rows:
    print(r)
    if r['state'] == 'idle in transaction' or r['blocked_by']:
        pids_to_kill.append(r['pid'])

for pid in pids_to_kill:
    print(f"Killing process {pid}")
    cursor.execute("SELECT pg_terminate_backend(%s)", (pid,))
    
conn.commit()
db.put_connection(conn)
print("Done")
