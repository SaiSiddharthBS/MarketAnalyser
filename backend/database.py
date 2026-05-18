"""
MarketPulse - Agent Alpha v2.0
Database Module — SQLite & Postgres setup and operations
"""
import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime
from config import DB_PATH

# Optional: PostgreSQL (only needed on cloud — Render/Neon)
try:
    import psycopg2
    import psycopg2.extras
    from psycopg2.pool import SimpleConnectionPool
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False
    psycopg2 = None
    SimpleConnectionPool = None

# Optional: dotenv (for loading .env files)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # Environment variables are set directly on cloud

# Load DATABASE_URL from env if available (for cloud)
DATABASE_URL = os.getenv("DATABASE_URL")
pool = None

if DATABASE_URL and HAS_POSTGRES:
    try:
        # Reduced to 5 to stay within Neon.tech free tier limits
        pool = SimpleConnectionPool(1, 5, DATABASE_URL)
        print("✅ Postgres Connection Pool initialized")
    except Exception as e:
        print(f"❌ Failed to initialize connection pool: {e}")
        pool = None  # Ensure it's explicitly None

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

def _prepare_query(query):
    """Convert SQLite syntax to Postgres syntax."""
    if not DATABASE_URL or not query:
        return query
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
    return query

def _execute_once(conn, query, params):
    """Execute a single query on the given connection. Returns result."""
    cur = get_cursor(conn)
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

def db_execute(query, params=None):
    """Universal executor for both SQLite and Postgres with auto-retry on stale connections."""
    conn = get_connection()
    if not conn:
        print(f"⚠️ Skipping query (no connection): {query[:50]}...")
        return [] if query.strip().upper().startswith("SELECT") else None

    query = _prepare_query(query)

    try:
        return _execute_once(conn, query, params)
    except Exception as e:
        err_msg = str(e).lower()
        is_connection_error = any(phrase in err_msg for phrase in [
            "ssl connection has been closed",
            "connection already closed",
            "server closed the connection",
            "connection reset",
            "broken pipe",
            "connection timed out",
        ])
        if is_connection_error and DATABASE_URL and pool:
            # Discard dead connection, get a fresh one, retry once
            print(f"🔄 DB connection lost, reconnecting... ({e})")
            try:
                pool.putconn(conn, close=True)
            except Exception:
                pass
            conn = get_connection()
            if not conn:
                return [] if query.strip().upper().startswith("SELECT") else None
            try:
                result = _execute_once(conn, query, params)
                print("✅ DB reconnection successful")
                return result
            finally:
                put_connection(conn)
        else:
            raise
    finally:
        try:
            put_connection(conn)
        except Exception:
            pass

def init_db():
    """Initialize all database tables (v2.0)."""
    conn = get_connection()
    cursor = get_cursor(conn)
    
    is_pg = bool(DATABASE_URL)
    id_col = "id SERIAL PRIMARY KEY" if is_pg else "id INTEGER PRIMARY KEY AUTOINCREMENT"
    now_func = "CURRENT_TIMESTAMP" if is_pg else "datetime('now')"
    
    # ─── EXISTING CORE TABLES ────────────────────────────────
    
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS holdings (
            {id_col},
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
            updated_at TEXT DEFAULT ({now_func})
        )
    """)

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS price_cache (
            {id_col},
            symbol TEXT NOT NULL,
            date TEXT NOT NULL,
            open REAL, high REAL, low REAL, close REAL,
            volume INTEGER,
            source TEXT DEFAULT 'yfinance',
            UNIQUE(symbol, date)
        )
    """)
    
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS portfolio_snapshots (
            {id_col},
            date TEXT NOT NULL UNIQUE,
            total_invested REAL NOT NULL,
            total_current REAL NOT NULL,
            total_return_pct REAL NOT NULL,
            holdings_json TEXT NOT NULL,
            market_data_json TEXT
        )
    """)
    
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS paper_trades (
            {id_col},
            symbol TEXT NOT NULL,
            trade_type TEXT NOT NULL DEFAULT 'BUY',
            status TEXT DEFAULT 'OPEN',
            signal_date TEXT NOT NULL,
            entry_date TEXT NOT NULL,
            entry_price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            position_value REAL NOT NULL,
            stop_loss REAL NOT NULL,
            target_price REAL NOT NULL,
            risk_reward_ratio REAL,
            exit_date TEXT,
            exit_price REAL,
            exit_reason TEXT,
            gross_pnl REAL,
            fees REAL,
            net_pnl REAL,
            return_pct REAL,
            regime_at_entry TEXT,
            ensemble_score REAL,
            conviction TEXT,
            model_votes_json TEXT,
            veto_status TEXT,
            autopsy_json TEXT,
            created_at TEXT DEFAULT ({now_func})
        )
    """)

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS paper_portfolio (
            {id_col},
            date TEXT UNIQUE NOT NULL,
            cash REAL NOT NULL,
            holdings_value REAL NOT NULL,
            total_equity REAL NOT NULL,
            open_positions INTEGER,
            daily_return_pct REAL,
            cumulative_return_pct REAL,
            drawdown_from_peak_pct REAL,
            benchmark_nifty_return_pct REAL,
            created_at TEXT DEFAULT ({now_func})
        )
    """)

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS paper_monthly_stats (
            {id_col},
            month TEXT UNIQUE NOT NULL,
            trades_taken INTEGER,
            wins INTEGER,
            losses INTEGER,
            win_rate REAL,
            total_pnl REAL,
            sharpe_ratio REAL,
            max_drawdown REAL,
            best_trade TEXT,
            worst_trade TEXT,
            nifty_return_pct REAL
        )
    """)

    # ─── PHASE 2: SELF-LEARNING TABLES ───────────────────────

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS prediction_log (
            {id_col},
            symbol TEXT NOT NULL,
            signal_date TEXT NOT NULL,
            signal_type TEXT,
            confidence REAL,
            ensemble_score REAL,
            model_votes_json TEXT,
            regime TEXT,
            vix_level REAL,
            day_of_week TEXT,
            sector TEXT,
            rvol REAL,
            outcome TEXT,
            actual_return_pct REAL,
            resolved_date TEXT,
            created_at TEXT DEFAULT ({now_func})
        )
    """)

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS learned_rules (
            {id_col},
            rule_type TEXT NOT NULL,
            condition_json TEXT NOT NULL,
            action_json TEXT NOT NULL,
            confidence REAL,
            sample_size INTEGER,
            discovered_date TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT ({now_func})
        )
    """)

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS regime_weights (
            {id_col},
            regime TEXT NOT NULL,
            weights_json TEXT NOT NULL,
            accuracy_data_json TEXT,
            updated_at TEXT DEFAULT ({now_func})
        )
    """)

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS calibration_log (
            {id_col},
            confidence_bucket TEXT NOT NULL,
            predicted_win_rate REAL,
            actual_win_rate REAL,
            sample_size INTEGER,
            calibration_factor REAL,
            updated_at TEXT DEFAULT ({now_func})
        )
    """)

    # ─── UPGRADED V2.0 TABLES ────────────────────────────────

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS signals (
            {id_col},
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
            status TEXT DEFAULT 'active'
        )
    """)

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS ml_predictions (
            {id_col},
            symbol TEXT NOT NULL,
            prediction_date TEXT NOT NULL,
            target_horizon_days INTEGER NOT NULL,
            prediction_class INTEGER,
            prob_up REAL NOT NULL,
            prob_down REAL NOT NULL,
            prob_flat REAL,
            expected_return REAL,
            feature_importance TEXT,
            created_at TEXT DEFAULT ({now_func})
        )
    """)

    # ─── NEW V2.0 TABLES ─────────────────────────────────────
    
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS market_regimes (
            {id_col},
            date TEXT NOT NULL UNIQUE,
            regime_name TEXT NOT NULL,
            confidence REAL NOT NULL,
            crisis_prob REAL,
            features_json TEXT,
            created_at TEXT DEFAULT ({now_func})
        )
    """)
    
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS veto_log (
            {id_col},
            date TEXT NOT NULL,
            symbol TEXT,
            veto_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            reason TEXT NOT NULL,
            duration_days INTEGER,
            expires_at TEXT,
            created_at TEXT DEFAULT ({now_func})
        )
    """)
    
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS error_log (
            {id_col},
            date TEXT NOT NULL,
            symbol TEXT NOT NULL,
            signal_type TEXT,
            actual_return REAL,
            error_category TEXT NOT NULL,
            description TEXT,
            model_agreement INTEGER,
            created_at TEXT DEFAULT ({now_func})
        )
    """)
    
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS model_performance (
            {id_col},
            date TEXT NOT NULL,
            model_name TEXT NOT NULL,
            rolling_accuracy REAL,
            baseline_accuracy REAL,
            decay_amount REAL,
            status TEXT,
            action_taken TEXT,
            created_at TEXT DEFAULT ({now_func})
        )
    """)
    
    # ─── UPGRADE 10 & 13: SIGNAL LOGGING & PAPER TRADES ───────────
    
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS signal_log (
            {id_col},
            timestamp TEXT NOT NULL,
            symbol TEXT NOT NULL,
            regime TEXT,
            signal_type TEXT NOT NULL,
            score INTEGER,
            confidence REAL,
            rsi REAL,
            rvol REAL,
            rr_ratio REAL,
            entry_price REAL,
            target_price REAL,
            conservative_target REAL,
            stop_loss REAL,
            qty INTEGER,
            holding_estimate TEXT,
            outcome TEXT,
            outcome_date TEXT,
            outcome_type TEXT,
            actual_pnl_pct REAL,
            created_at TEXT DEFAULT ({now_func})
        )
    """)

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS paper_trades (
            {id_col},
            signal_id INTEGER,
            symbol TEXT NOT NULL,
            entry_price REAL NOT NULL,
            entry_date TEXT NOT NULL,
            target_price REAL,
            stop_loss REAL,
            qty INTEGER NOT NULL,
            status TEXT DEFAULT 'OPEN',
            exit_price REAL,
            exit_date TEXT,
            pnl_absolute REAL,
            pnl_pct REAL,
            notes TEXT,
            created_at TEXT DEFAULT ({now_func})
        )
    """)

    # ─── DAILY PREDICTIONS TABLE (Bug Fix: was missing entirely) ──────
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS daily_predictions (
            {id_col},
            symbol TEXT NOT NULL,
            target_date TEXT NOT NULL,
            pred_high REAL NOT NULL,
            pred_low REAL NOT NULL,
            pred_support REAL,
            pred_resistance REAL,
            pred_direction TEXT,
            actual_open REAL,
            actual_high REAL,
            actual_low REAL,
            actual_close REAL,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT ({now_func})
        )
    """)

    conn.commit()
    put_connection(conn)

    # ─── SAFE MIGRATIONS: Add missing columns to existing tables ──────
    # Each migration uses its own connection + commit/rollback cycle.
    migrations = [
        "ALTER TABLE daily_predictions ADD COLUMN pred_support REAL",
        "ALTER TABLE daily_predictions ADD COLUMN pred_resistance REAL",
        "ALTER TABLE daily_predictions ADD COLUMN pred_direction TEXT",
        "ALTER TABLE daily_predictions ADD COLUMN actual_open REAL",
        "ALTER TABLE daily_predictions ADD COLUMN actual_high REAL",
        "ALTER TABLE daily_predictions ADD COLUMN actual_low REAL",
        "ALTER TABLE daily_predictions ADD COLUMN actual_close REAL",
        "ALTER TABLE daily_predictions ADD COLUMN created_at TEXT",
        "ALTER TABLE signal_log ADD COLUMN timestamp TEXT",
        "ALTER TABLE signal_log ADD COLUMN regime TEXT",
        "ALTER TABLE signal_log ADD COLUMN signal_type TEXT",
        "ALTER TABLE signal_log ADD COLUMN score INTEGER",
        "ALTER TABLE signal_log ADD COLUMN confidence REAL",
        "ALTER TABLE signal_log ADD COLUMN rsi REAL",
        "ALTER TABLE signal_log ADD COLUMN rvol REAL",
        "ALTER TABLE signal_log ADD COLUMN rr_ratio REAL",
        "ALTER TABLE signal_log ADD COLUMN entry_price REAL",
        "ALTER TABLE signal_log ADD COLUMN target_price REAL",
        "ALTER TABLE signal_log ADD COLUMN conservative_target REAL",
        "ALTER TABLE signal_log ADD COLUMN stop_loss REAL",
        "ALTER TABLE signal_log ADD COLUMN qty INTEGER",
        "ALTER TABLE signal_log ADD COLUMN holding_estimate TEXT",
        "ALTER TABLE signal_log ADD COLUMN outcome TEXT",
        "ALTER TABLE signal_log ADD COLUMN outcome_date TEXT",
        "ALTER TABLE signal_log ADD COLUMN outcome_type TEXT",
        "ALTER TABLE signal_log ADD COLUMN actual_pnl_pct REAL",
        "ALTER TABLE signal_log ADD COLUMN date_generated TEXT",
    ]
    for migration in migrations:
        m_conn = get_connection()
        if not m_conn:
            continue
        try:
            m_cur = get_cursor(m_conn)
            m_cur.execute(migration)
            m_conn.commit()
            m_cur.close()
        except Exception:
            try:
                m_conn.rollback()
            except Exception:
                pass
        finally:
            put_connection(m_conn)

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

# --- Restored CRUD Operations ---

def get_holdings():
    return db_execute("SELECT * FROM holdings ORDER BY created_at DESC")

def get_model_performance():
    query = "SELECT * FROM model_performance ORDER BY date DESC LIMIT 50"
    return db_execute(query)

def log_signal(signal_data: dict):
    """Upgrade 10: Log every generated signal to the database."""
    query = """
        INSERT INTO signal_log (
            timestamp, symbol, regime, signal_type, score, confidence,
            rsi, rvol, rr_ratio, entry_price, target_price, conservative_target,
            stop_loss, qty, holding_estimate, date_generated
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    # Safely extract rr_ratio from "1:2.5" format
    rr_str = signal_data.get("risk_reward", "1:0")
    try:
        rr_ratio = float(rr_str.split(":")[1])
    except:
        rr_ratio = 0.0
        
    now_iso = datetime.now().isoformat()
    params = (
        now_iso,
        signal_data.get("symbol"),
        signal_data.get("regime", "UNKNOWN"),
        signal_data.get("signal_label", signal_data.get("signal")),
        signal_data.get("score"),
        signal_data.get("allocation_pct", 0) * 100, # Approximate mapping
        signal_data.get("metrics", {}).get("rsi", 0),
        signal_data.get("metrics", {}).get("rvol", 0),
        rr_ratio,
        signal_data.get("entry", 0),
        signal_data.get("target", 0),
        signal_data.get("conservative_target", 0),
        signal_data.get("stop_loss", 0),
        0, # qty is calculated frontend side right now
        signal_data.get("holding_period", ""),
        now_iso  # date_generated
    )
    db_execute(query, params)

def log_screener_signals(results, segment=None):
    """Upgrade 10: Log every generated signal to the database from screener."""
    for result in results:
        # Only log valid BUY or SELL signals to prevent database bloat
        if result.get("signal") in ["BUY", "SELL", "STRONG_BUY", "STRONG_SELL"]:
            log_signal(result)

def add_holding(symbol, name, asset_type, quantity, buy_price, buy_date, invested_amount, exchange="NSE", scheme_code=None, notes=None):
    query = """INSERT INTO holdings 
               (symbol, name, asset_type, exchange, quantity, buy_price, buy_date, invested_amount, scheme_code, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
    return db_execute(query, (symbol, name, asset_type, exchange, quantity, buy_price, buy_date, invested_amount, scheme_code, notes))

def delete_holding(holding_id):
    return db_execute("DELETE FROM holdings WHERE id = ?", (holding_id,))

def get_active_signals():
    return db_execute("SELECT * FROM signals WHERE status = 'active' ORDER BY created_at DESC LIMIT 50")

def get_paper_portfolio():
    positions = db_execute("SELECT * FROM paper_trades WHERE status = 'OPEN'") or []
    history = db_execute("SELECT * FROM paper_trades WHERE status = 'CLOSED' ORDER BY trade_date DESC LIMIT 50") or []
    metrics_res = db_execute("SELECT SUM(pnl) as net_realized_pnl, SUM(fees) as total_fees FROM paper_trades WHERE status = 'CLOSED'")
    metrics = metrics_res[0] if metrics_res else {"net_realized_pnl": 0, "total_fees": 0}
    if not metrics.get("net_realized_pnl"): metrics["net_realized_pnl"] = 0
    if not metrics.get("total_fees"): metrics["total_fees"] = 0
    return {"positions": positions, "history": history, "metrics": metrics}

def add_paper_trade(symbol, trade_type, quantity, price, fees, notes=None):
    query = """INSERT INTO paper_trades (symbol, trade_type, quantity, price, fees, notes)
               VALUES (?, ?, ?, ?, ?, ?)"""
    return db_execute(query, (symbol, trade_type, quantity, price, fees, notes))

def get_recent_intraday_verification(symbol):
    """Get the most recent VERIFIED prediction for a symbol (status != 'pending')."""
    try:
        res = db_execute(
            "SELECT * FROM daily_predictions WHERE symbol = ? AND status != 'pending' ORDER BY created_at DESC LIMIT 1",
            (symbol,)
        )
        return res[0] if res else None
    except Exception as e:
        print(f"Verification lookup failed for {symbol}: {e}")
        return None

def save_intraday_prediction(symbol, pred_high, pred_low, pred_support, pred_resistance, pred_direction, target_date):
    """Save a new intraday prediction for grading tomorrow."""
    try:
        from datetime import datetime
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        # Avoid duplicates for same symbol + date
        existing = db_execute(
            "SELECT id FROM daily_predictions WHERE symbol = ? AND target_date = ?",
            (symbol, target_date)
        )
        if existing:
            return  # Already have a prediction for this symbol/date
        
        # Include date_predicted for PostgreSQL compatibility (legacy column)
        db_execute(
            """INSERT INTO daily_predictions 
               (symbol, date_predicted, target_date, pred_high, pred_low, pred_support, pred_resistance, pred_direction, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (symbol, today_str, target_date, pred_high, pred_low, pred_support, pred_resistance, pred_direction, today_str)
        )
    except Exception as e:
        print(f"Failed to save prediction for {symbol}: {e}")

def log_screener_signals(results, segment="NIFTY_50"):
    pass # Reserved for future ML logging

