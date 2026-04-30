import os
import psycopg2
from config import USER_MF_HOLDINGS

def seed():
    url = os.getenv('DATABASE_URL')
    if not url:
        print("Error: DATABASE_URL not set")
        return
        
    conn = psycopg2.connect(url)
    cur = conn.cursor()
    
    # Clear existing
    cur.execute('DELETE FROM holdings')
    
    # Insert correct ones
    for name, info in USER_MF_HOLDINGS.items():
        cur.execute(
            'INSERT INTO holdings (symbol, name, asset_type, quantity, buy_price, buy_date, invested_amount, scheme_code) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
            (info['scheme_code'], name, 'mf', info['units'], 0, '2025-01-01', info['invested'], info['scheme_code'])
        )
    
    conn.commit()
    conn.close()
    print("✅ Cloud holdings synced withIndmoney screenshot values.")

if __name__ == "__main__":
    seed()
