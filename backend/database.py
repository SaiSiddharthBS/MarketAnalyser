"""
MarketPulse - Agent Alpha
Database Module — SQLite setup and operations
"""
import sqlite3
import json
import os
import psycopg2
import psycopg2.extras
from psycopg2.pool import SimpleConnectionPool
from pathlib import Path
from datetime import datetime
from config import DB_PATH
from dotenv import load_dotenv

load_dotenv()

# Load DATABASE_URL from env if available (for cloud)
DATABASE_URL = os.getenv("DATABASE_URL")
pool = None

if DATABASE_URL:
    try:
        # Reduced to 5 to stay within Neon.tech free tier limits
        pool = SimpleConnectionPool(1, 5, DATABASE_URL)
        print("✅ Postgres Connection Pool initialized")
    except Exception as e:
        print(f"❌ Failed to initialize connection pool: {e}")
        pool = None # Ensure it's explicitly None

def get_connection():
    """Get a connection (Postgres or SQLite)."""
    if DATABASE_URL and pool:
        try:
            return pool.getconn()
        except Exception as e:
            print(f"❌ Pool getconn error: {e}")
            return None
    else:
        # SQLite Connection (Local)
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

def put_connection(conn):
    """Return a connection to the pool or close it."""
    if DATABASE_URL and pool and conn:
        try:
            pool.putconn(conn)
        except Exception:
            pass
    elif conn:
        conn.close()

def get_cursor(conn):
    """Get a cursor (RealDictCursor for Postgres, standard for SQLite)."""
    if DATABASE_URL:
        return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    return conn.cursor()

def db_execute(query, params=None):
    """Universal executor for both SQLite and Postgres."""
    conn = get_connection()
    if not conn:
        print(f"⚠️ Skipping query (no connection): {query[:50]}...")
        return [] if query.strip().upper().startswith("SELECT") else None
        
    cur = get_cursor(conn)
    
    # Convert '?' to '%s' for Postgres
    if DATABASE_URL and query:
        query = query.replace("?", "%s")
        # Convert INSERT OR REPLACE to Postgres ON CONFLICT
        if "INSERT OR REPLACE INTO price_cache" in query:
             query = query.replace("INSERT OR REPLACE INTO", "INSERT INTO") + " ON CONFLICT (symbol, date) DO UPDATE SET open=EXCLUDED.open, high=EXCLUDED.high, low=EXCLUDED.low, close=EXCLUDED.close, volume=EXCLUDED.volume"
        elif "INSERT OR REPLACE INTO mf_nav_cache" in query:
             query = query.replace("INSERT OR REPLACE INTO", "INSERT INTO") + " ON CONFLICT (scheme_code, date) DO UPDATE SET nav=EXCLUDED.nav"
        elif "INSERT OR REPLACE INTO portfolio_snapshots" in query:
             query = query.replace("INSERT OR REPLACE INTO", "INSERT INTO") + " ON CONFLICT (date) DO UPDATE SET total_invested=EXCLUDED.total_invested, total_current=EXCLUDED.total_current, total_return_pct=EXCLUDED.total_return_pct, holdings_json=EXCLUDED.holdings_json, market_data_json=EXCLUDED.market_data_json"
             
        if "datetime('now')" in query:
            query = query.replace("datetime('now')", "CURRENT_TIMESTAMP")
             
    try:
        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)
        
        if query.strip().upper().startswith("SELECT"):
            res = cur.fetchall()
            return [dict(r) for r in res]
        else:
            conn.commit()
            return True
    finally:
        cur.close()
        put_connection(conn)

def init_db():
    """Initialize all database tables."""
    conn = get_connection()
    cursor = get_cursor(conn)
    
    # Use SERIAL for Postgres, AUTOINCREMENT for SQLite
    id_type = "SERIAL" if DATABASE_URL else "INTEGER PRIMARY KEY AUTOINCREMENT"
    pk_constraint = "" if DATABASE_URL else "" # Handled by id_type
    
    # For simplicity in migration, we use the same schema but adapted
    # Portfolio holdings
    now_func = "CURRENT_TIMESTAMP" if DATABASE_URL else "datetime('now')"
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS holdings (
            id {id_type},
            symbol TEXT NOT NULL,
            name TEXT NOT NULL,
            asset_type TEXT NOT NULL,
            exchange TEXT DEFAULT 'NSE',
            quantity REAL NOT NULL,
            buy_price REAL NOT NULL,
            buy_date TEXT NOT NULL,
            invested_amount REAL NOT NULL,
            scheme_code TEXT,
            notes TEXT,
            created_at TEXT DEFAULT ({now_func}),
            updated_at TEXT DEFAULT ({now_func}),
            {"PRIMARY KEY (id)" if DATABASE_URL else ""}
        )
    """)

    # Price cache for stocks/indices
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS price_cache (
            id {id_type},
            symbol TEXT NOT NULL,
            date TEXT NOT NULL,
            open REAL, high REAL, low REAL, close REAL,
            volume INTEGER,
            source TEXT DEFAULT 'yfinance',
            {"PRIMARY KEY (id)," if DATABASE_URL else ""}
            UNIQUE(symbol, date)
        )
    """)

    # MF NAV cache
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS mf_nav_cache (
            id {id_type},
            scheme_code TEXT NOT NULL,
            date TEXT NOT NULL,
            nav REAL NOT NULL,
            {"PRIMARY KEY (id)," if DATABASE_URL else ""}
            UNIQUE(scheme_code, date)
        )
    """)

    # Signals generated by the system
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS signals (
            id {id_type},
            symbol TEXT NOT NULL,
            signal_type TEXT NOT NULL,
            confidence REAL NOT NULL,
            entry_price REAL,
            target_price REAL,
            stop_loss REAL,
            position_size_pct REAL,
            reasoning TEXT,
            factors TEXT,
            created_at TEXT DEFAULT ({now_func}),
            expiry_date TEXT,
            status TEXT DEFAULT 'active',
            {"PRIMARY KEY (id)" if DATABASE_URL else ""}
        )
    """)

    # ML Predictions
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS ml_predictions (
            id {id_type},
            symbol TEXT NOT NULL,
            prediction_date TEXT NOT NULL,
            target_horizon_days INTEGER NOT NULL,
            prob_up REAL NOT NULL,
            prob_down REAL NOT NULL,
            expected_return REAL,
            feature_importance TEXT,
            created_at TEXT DEFAULT ({now_func}),
            {"PRIMARY KEY (id)" if DATABASE_URL else ""}
        )
    """)

    # Paper Trades (Simulated Portfolio)
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS paper_trades (
            id {id_type},
            symbol TEXT NOT NULL,
            trade_type TEXT NOT NULL,
            quantity REAL NOT NULL,
            price REAL NOT NULL,
            fees REAL NOT NULL,
            trade_date TEXT DEFAULT ({now_func}),
            status TEXT DEFAULT 'OPEN',
            pnl REAL DEFAULT 0,
            notes TEXT,
            {"PRIMARY KEY (id)" if DATABASE_URL else ""}
        )
    """)
    
    # Portfolio snapshots
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS portfolio_snapshots (
            id {id_type},
            date TEXT NOT NULL UNIQUE,
            total_invested REAL NOT NULL,
            total_current REAL NOT NULL,
            total_return_pct REAL NOT NULL,
            holdings_json TEXT NOT NULL,
            market_data_json TEXT,
            {"PRIMARY KEY (id)" if DATABASE_URL else ""}
        )
    """)

    # Watchlist
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS watchlist (
            id {id_type},
            symbol TEXT NOT NULL UNIQUE,
            name TEXT,
            added_at TEXT DEFAULT ({now_func}),
            notes TEXT,
            {"PRIMARY KEY (id)" if DATABASE_URL else ""}
        )
    """)

    # Market data cache (indices, macro)
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS market_data (
            id {id_type},
            indicator TEXT NOT NULL,
            date TEXT NOT NULL,
            value REAL NOT NULL,
            source TEXT,
            {"PRIMARY KEY (id)," if DATABASE_URL else ""}
            UNIQUE(indicator, date)
        )
    """)

    # Signal log for accuracy tracking (Day 1 logging)
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS signal_log (
            id {id_type},
            date_generated TEXT NOT NULL,
            symbol TEXT NOT NULL,
            segment TEXT,
            signal_type TEXT NOT NULL,
            score INTEGER NOT NULL,
            entry_price REAL,
            target_price REAL,
            stop_loss REAL,
            risk_reward REAL,
            holding_period TEXT,
            actual_open REAL,
            actual_high REAL,
            actual_low REAL,
            actual_close REAL,
            outcome TEXT DEFAULT 'open',
            days_to_outcome INTEGER,
            created_at TEXT DEFAULT ({now_func}),
            {"PRIMARY KEY (id)" if DATABASE_URL else ""}
        )
    """)

    # Daily Intraday Predictions (For Verification Engine)
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS daily_predictions (
            id {id_type},
            symbol TEXT NOT NULL,
            date_predicted TEXT NOT NULL,
            target_date TEXT NOT NULL,
            pred_high REAL NOT NULL,
            pred_low REAL NOT NULL,
            pred_direction TEXT,
            actual_open REAL,
            actual_high REAL,
            actual_low REAL,
            actual_close REAL,
            status TEXT DEFAULT 'pending',
            {"PRIMARY KEY (id)," if DATABASE_URL else ""}
            UNIQUE(symbol, target_date)
        )
    """)

    conn.commit()
    put_connection(conn)
    print("✅ Database initialized successfully")


def log_screener_signals(results, segment="NIFTY_50"):
    """Log screener results to signal_log for accuracy tracking."""
    if not results:
        return
    conn = get_connection()
    if not conn:
        return
    cursor = get_cursor(conn)
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        for r in results:
            db_execute(cursor, """
                INSERT INTO signal_log 
                (date_generated, symbol, segment, signal_type, score, entry_price, target_price, stop_loss, risk_reward, holding_period)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (today, r["symbol"], segment, r["signal"], r["score"],
                  r["entry"], r["target"], r["stop_loss"],
                  r.get("risk_reward", 0), r.get("holding_period", "N/A")))
        conn.commit()
        print(f"✅ Logged {len(results)} signals to signal_log")
    except Exception as e:
        print(f"❌ Failed to log signals: {e}")
    finally:
        put_connection(conn)

def log_intraday_prediction(symbol, target_date, pred_high, pred_low, pred_direction):
    """Log an intraday prediction (Peak/Floor) for tomorrow."""
    today = datetime.now().strftime("%Y-%m-%d")
    query = "INSERT OR REPLACE INTO daily_predictions (symbol, date_predicted, target_date, pred_high, pred_low, pred_direction, status) VALUES (?, ?, ?, ?, ?, ?, 'pending')"
    if DATABASE_URL:
        query = "INSERT INTO daily_predictions (symbol, date_predicted, target_date, pred_high, pred_low, pred_direction, status) VALUES (?, ?, ?, ?, ?, ?, 'pending') ON CONFLICT (symbol, target_date) DO UPDATE SET pred_high=EXCLUDED.pred_high, pred_low=EXCLUDED.pred_low, pred_direction=EXCLUDED.pred_direction, date_predicted=EXCLUDED.date_predicted"
    
    try:
        db_execute(query, (symbol, today, target_date, pred_high, pred_low, pred_direction))
    except Exception as e:
        print(f"⚠️ Failed to log intraday prediction for {symbol}: {e}")

def get_recent_intraday_verification(symbol):
    """Get the most recent verified intraday prediction for a symbol."""
    try:
        # Get the most recent prediction that has actuals recorded (status != pending)
        res = db_execute(
            "SELECT * FROM daily_predictions WHERE symbol = ? AND status != 'pending' ORDER BY target_date DESC LIMIT 1",
            (symbol,)
        )
        if res and len(res) > 0:
            return res[0]
        return None
    except Exception as e:
        print(f"⚠️ Failed to get recent verification for {symbol}: {e}")
        return None


# ── CRUD Operations ──────────────────────────────────────────

def add_holding(symbol, name, asset_type, quantity, buy_price, buy_date, invested_amount, exchange="NSE", scheme_code=None, notes=None):
    """Add a new holding to the portfolio."""
    # Ensure asset_type is lowercase but allow ANY asset class (Crypto, Real Estate, PPF, NPS, Commodities, etc.)
    # The AI Advisor will dynamically interpret whatever asset class the user inputs.
    asset_type = str(asset_type).strip().lower() if asset_type else "other"
        
    db_execute("""
        INSERT INTO holdings 
        (symbol, name, asset_type, quantity, buy_price, buy_date, invested_amount, exchange, scheme_code, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (symbol, name, asset_type, quantity, buy_price, buy_date, invested_amount, exchange, scheme_code, notes))


def get_holdings(asset_type=None):
    """Get all holdings, optionally filtered by type."""
    if asset_type:
        return db_execute("SELECT * FROM holdings WHERE asset_type = ?", (asset_type,))
    else:
        return db_execute("SELECT * FROM holdings ORDER BY asset_type, invested_amount DESC")


def update_holding(holding_id, **kwargs):
    """Update a holding's fields."""
    allowed = {"quantity", "buy_price", "invested_amount", "notes"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if updates:
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        now_func = "CURRENT_TIMESTAMP" if DATABASE_URL else "datetime('now')"
        values = list(updates.values()) + [holding_id]
        db_execute(f"UPDATE holdings SET {set_clause}, updated_at = {now_func} WHERE id = ?", values)


def delete_holding(holding_id):
    """Remove a holding."""
    db_execute("DELETE FROM holdings WHERE id = ?", (holding_id,))


# ── Paper Trading Operations ──────────────────────────────────────────

def add_paper_trade(symbol, trade_type, quantity, price, fees, notes=None):
    """Record a paper trade."""
    db_execute(
        """INSERT INTO paper_trades (symbol, trade_type, quantity, price, fees, notes)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (symbol, trade_type, quantity, price, fees, notes)
    )

def get_paper_portfolio():
    """Calculate current paper trading positions and history."""
    trades = db_execute("SELECT * FROM paper_trades ORDER BY trade_date ASC")
    
    positions = {}
    total_realized_pnl = 0
    total_fees = 0
    
    for t in trades:
        sym = t["symbol"]
        qty = t["quantity"]
        price = t["price"]
        ttype = t["trade_type"]
        fees = t["fees"]
        
        total_fees += fees
        
        if sym not in positions:
            positions[sym] = {"symbol": sym, "quantity": 0, "avg_price": 0, "invested": 0}
            
        pos = positions[sym]
        
        if ttype == "BUY":
            total_cost = (pos["quantity"] * pos["avg_price"]) + (qty * price)
            pos["quantity"] += qty
            pos["avg_price"] = total_cost / pos["quantity"] if pos["quantity"] > 0 else 0
            pos["invested"] = pos["quantity"] * pos["avg_price"]
        elif ttype == "SELL":
            if pos["quantity"] >= qty:
                realized_pnl = (price - pos["avg_price"]) * qty
                total_realized_pnl += realized_pnl
                
                pos["quantity"] -= qty
                pos["invested"] = pos["quantity"] * pos["avg_price"]
                
                if pos["quantity"] == 0:
                    pos["avg_price"] = 0
            else:
                pos["quantity"] = 0
                pos["avg_price"] = 0
                pos["invested"] = 0

    active_positions = [p for p in positions.values() if p["quantity"] > 0]
    
    return {
        "positions": active_positions,
        "history": trades[::-1], # Reverse chronological
        "metrics": {
            "realized_pnl": total_realized_pnl,
            "total_fees": total_fees,
            "net_realized_pnl": total_realized_pnl - total_fees
        }
    }


def save_signal(symbol, signal_type, confidence, entry_price=None, target_price=None, stop_loss=None, position_size_pct=None, reasoning=None, factors=None, expiry_date=None):
    """Save a generated signal."""
    db_execute(
        """INSERT INTO signals (symbol, signal_type, confidence, entry_price, target_price, stop_loss, position_size_pct, reasoning, factors, expiry_date)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (symbol, signal_type, confidence, entry_price, target_price, stop_loss, position_size_pct, reasoning, json.dumps(factors) if factors else None, expiry_date),
    )


def get_active_signals():
    """Get all currently active signals."""
    return db_execute("SELECT * FROM signals WHERE status = 'active' ORDER BY confidence DESC")


def cache_price(symbol, date, open_p, high, low, close, volume, source="yfinance"):
    """Cache a price data point."""
    db_execute(
        """INSERT OR REPLACE INTO price_cache (symbol, date, open, high, low, close, volume, source)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (symbol, date, open_p, high, low, close, volume, source),
    )


def save_portfolio_snapshot(date, total_invested, total_current, total_return_pct, holdings_json, market_data_json=None):
    """Save a daily snapshot of the portfolio."""
    db_execute(
        """INSERT OR REPLACE INTO portfolio_snapshots (date, total_invested, total_current, total_return_pct, holdings_json, market_data_json)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (date, total_invested, total_current, total_return_pct, holdings_json, market_data_json)
    )

def get_latest_portfolio_snapshot():
    """Get the most recent portfolio snapshot."""
    rows = db_execute("SELECT * FROM portfolio_snapshots ORDER BY date DESC LIMIT 1")
    return rows[0] if rows else None

def get_portfolio_history(days=30):
    """Get portfolio history for charting."""
    return db_execute("SELECT date, total_current, total_return_pct FROM portfolio_snapshots ORDER BY date ASC LIMIT ?", (days,))


if __name__ == "__main__":
    init_db()
