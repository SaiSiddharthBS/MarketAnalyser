"""
MarketPulse - Agent Alpha v2.0
Database Module — SQLite & Postgres setup and operations
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
        elif "INSERT OR REPLACE INTO market_regimes" in query:
             query = query.replace("INSERT OR REPLACE INTO", "INSERT INTO") + " ON CONFLICT (date) DO UPDATE SET regime_name=EXCLUDED.regime_name, confidence=EXCLUDED.confidence, crisis_prob=EXCLUDED.crisis_prob, features_json=EXCLUDED.features_json"
             
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
    """Initialize all database tables (v2.0)."""
    conn = get_connection()
    cursor = get_cursor(conn)
    
    id_type = "SERIAL" if DATABASE_URL else "INTEGER PRIMARY KEY AUTOINCREMENT"
    now_func = "CURRENT_TIMESTAMP" if DATABASE_URL else "datetime('now')"
    
    # ─── EXISTING CORE TABLES (Unchanged) ────────────────────
    
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

    # ─── UPGRADED V2.0 TABLES ────────────────────────────────

    # Signals table (Upgraded for Ensemble v2)
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS signals (
            id {id_type},
            symbol TEXT NOT NULL,
            signal_type TEXT NOT NULL,
            confidence REAL NOT NULL,
            ensemble_score REAL,
            kelly_multiplier REAL,
            entry_price REAL,
            target_price REAL,
            stop_loss REAL,
            position_size_pct REAL,
            reasoning TEXT,
            model_votes_json TEXT,
            veto_status TEXT,
            created_at TEXT DEFAULT ({now_func}),
            expiry_date TEXT,
            status TEXT DEFAULT 'active',
            {"PRIMARY KEY (id)" if DATABASE_URL else ""}
        )
    """)

    # ML Predictions (Upgraded for LightGBM Walk-Forward)
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS ml_predictions (
            id {id_type},
            symbol TEXT NOT NULL,
            prediction_date TEXT NOT NULL,
            target_horizon_days INTEGER NOT NULL,
            prediction_class INTEGER,
            prob_up REAL NOT NULL,
            prob_down REAL NOT NULL,
            prob_flat REAL,
            expected_return REAL,
            feature_importance TEXT,
            created_at TEXT DEFAULT ({now_func}),
            {"PRIMARY KEY (id)" if DATABASE_URL else ""}
        )
    """)

    # ─── NEW V2.0 TABLES ─────────────────────────────────────
    
    # 1. Regime Classifier Tracking
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS market_regimes (
            id {id_type},
            date TEXT NOT NULL UNIQUE,
            regime_name TEXT NOT NULL,
            confidence REAL NOT NULL,
            crisis_prob REAL,
            features_json TEXT,
            created_at TEXT DEFAULT ({now_func}),
            {"PRIMARY KEY (id)" if DATABASE_URL else ""}
        )
    """)
    
    # 2. Hard Veto Log (Compliance & Audit)
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS veto_log (
            id {id_type},
            date TEXT NOT NULL,
            symbol TEXT,
            veto_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            reason TEXT NOT NULL,
            duration_days INTEGER,
            expires_at TEXT,
            created_at TEXT DEFAULT ({now_func}),
            {"PRIMARY KEY (id)" if DATABASE_URL else ""}
        )
    """)
    
    # 3. Error Analysis Engine
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS error_log (
            id {id_type},
            date TEXT NOT NULL,
            symbol TEXT NOT NULL,
            signal_type TEXT,
            actual_return REAL,
            error_category TEXT NOT NULL,
            description TEXT,
            model_agreement INTEGER,
            created_at TEXT DEFAULT ({now_func}),
            {"PRIMARY KEY (id)" if DATABASE_URL else ""}
        )
    """)
    
    # 4. Alpha Decay Monitoring
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS model_performance (
            id {id_type},
            date TEXT NOT NULL,
            model_name TEXT NOT NULL,
            rolling_accuracy REAL,
            baseline_accuracy REAL,
            decay_amount REAL,
            status TEXT,
            action_taken TEXT,
            created_at TEXT DEFAULT ({now_func}),
            {"PRIMARY KEY (id)" if DATABASE_URL else ""}
        )
    """)

    conn.commit()
    put_connection(conn)
    print("✅ Database (v2.0) initialized successfully")

# ── CRUD Operations ──────────────────────────────────────────

def save_ensemble_signal(symbol, signal_data):
    """Save a v2.0 ensemble signal."""
    db_execute(
        """INSERT INTO signals (
            symbol, signal_type, confidence, ensemble_score, kelly_multiplier,
            reasoning, model_votes_json, veto_status
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            symbol, 
            signal_data.get("signal", "UNKNOWN"), 
            signal_data.get("final_confidence", 0),
            signal_data.get("ensemble_score", 0),
            signal_data.get("kelly_multiplier", 0),
            signal_data.get("action", ""),
            json.dumps(signal_data.get("model_votes", {})),
            signal_data.get("veto_override", "NONE")
        ),
    )

def log_veto(veto_data):
    """Log a hard veto event."""
    today = datetime.now().strftime("%Y-%m-%d")
    db_execute(
        """INSERT INTO veto_log (
            date, symbol, veto_type, severity, reason, duration_days, expires_at
           ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            today,
            veto_data.get("symbol", "MARKET"),
            veto_data.get("type", "UNKNOWN"),
            veto_data.get("severity", "HIGH"),
            veto_data.get("reason", ""),
            veto_data.get("duration_days", 0),
            veto_data.get("expires")
        )
    )

def log_market_regime(regime_data):
    """Log daily market regime state."""
    today = datetime.now().strftime("%Y-%m-%d")
    query = "INSERT OR REPLACE INTO market_regimes (date, regime_name, confidence, crisis_prob, features_json) VALUES (?, ?, ?, ?, ?)"
    if DATABASE_URL:
        query = "INSERT INTO market_regimes (date, regime_name, confidence, crisis_prob, features_json) VALUES (?, ?, ?, ?, ?) ON CONFLICT (date) DO UPDATE SET regime_name=EXCLUDED.regime_name, confidence=EXCLUDED.confidence, crisis_prob=EXCLUDED.crisis_prob, features_json=EXCLUDED.features_json"
        
    db_execute(
        query,
        (
            today,
            regime_data.get("regime", "unknown"),
            regime_data.get("confidence_pct", 0),
            regime_data.get("crisis_probability_tomorrow_pct", 0),
            json.dumps(regime_data.get("features", {}))
        )
    )

# Keeping backward compatibility for existing scripts
def save_signal(*args, **kwargs):
    pass # Migrating to save_ensemble_signal

if __name__ == "__main__":
    init_db()
