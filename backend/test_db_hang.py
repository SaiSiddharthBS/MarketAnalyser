import database as db
print("Patching cursor execute to print queries...")
original_execute = db.get_cursor.__code__ # not that easy
# Let's just redefine init_db but with prints
import sys

conn = db.get_connection()
cursor = db.get_cursor(conn)
is_pg = bool(db.DATABASE_URL)
id_col = "id SERIAL PRIMARY KEY" if is_pg else "id INTEGER PRIMARY KEY AUTOINCREMENT"
now_func = "CURRENT_TIMESTAMP" if is_pg else "datetime('now')"

queries = [
    f"""
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
    """,
    f"""
        CREATE TABLE IF NOT EXISTS price_cache (
            {id_col},
            symbol TEXT NOT NULL,
            date TEXT NOT NULL,
            open REAL, high REAL, low REAL, close REAL,
            volume INTEGER,
            source TEXT DEFAULT 'yfinance',
            UNIQUE(symbol, date)
        )
    """,
    f"""
        CREATE TABLE IF NOT EXISTS portfolio_snapshots (
            {id_col},
            date TEXT NOT NULL UNIQUE,
            total_invested REAL NOT NULL,
            total_current REAL NOT NULL,
            total_return_pct REAL NOT NULL,
            holdings_json TEXT NOT NULL,
            market_data_json TEXT
        )
    """,
    f"""
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
    """,
    f"""
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
    """,
    f"""
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
    """,
    f"""
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
    """,
    f"""
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
    """,
    f"""
        CREATE TABLE IF NOT EXISTS regime_weights (
            {id_col},
            regime TEXT NOT NULL,
            weights_json TEXT NOT NULL,
            accuracy_data_json TEXT,
            updated_at TEXT DEFAULT ({now_func})
        )
    """,
    f"""
        CREATE TABLE IF NOT EXISTS calibration_log (
            {id_col},
            confidence_bucket TEXT NOT NULL,
            predicted_win_rate REAL,
            actual_win_rate REAL,
            sample_size INTEGER,
            calibration_factor REAL,
            updated_at TEXT DEFAULT ({now_func})
        )
    """,
    f"""
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
    """,
    f"""
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
    """,
    f"""
        CREATE TABLE IF NOT EXISTS market_regimes (
            {id_col},
            date TEXT NOT NULL UNIQUE,
            regime_name TEXT NOT NULL,
            confidence REAL NOT NULL,
            crisis_prob REAL,
            features_json TEXT,
            created_at TEXT DEFAULT ({now_func})
        )
    """,
    f"""
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
    """,
    f"""
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
    """,
    f"""
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
    """,
    f"""
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
    """,
    f"""
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
    """,
    f"""
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
    """
]

for i, q in enumerate(queries):
    print(f"Executing Create Table Query {i+1}...")
    cursor.execute(q)
    print(f"Done Create Table Query {i+1}")
    
conn.commit()
db.put_connection(conn)

print("Starting migrations...")

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

for i, migration in enumerate(migrations):
    print(f"Migration {i+1}: {migration}")
    m_conn = db.get_connection()
    if not m_conn:
        continue
    try:
        m_cur = db.get_cursor(m_conn)
        m_cur.execute(migration)
        m_conn.commit()
        m_cur.close()
    except Exception as e:
        print(f"Failed (expected if col exists): {e}")
        try:
            m_conn.rollback()
        except Exception:
            pass
    finally:
        db.put_connection(m_conn)
        
print("All done!")
