"""
MarketPulse — Accuracy Analyser
Tracks signal outcomes and generates performance metrics.
Compares predicted signals with actual market outcomes.
"""
from datetime import datetime, timedelta
from data.stock_fetcher import download_ohlcv
import database as db


def update_signal_outcomes():
    """Check open signals and update outcomes based on actual price data.
    Run this daily after market close (e.g., 4 PM IST).
    """
    conn = db.get_connection()
    if not conn:
        return {"updated": 0, "error": "No DB connection"}

    cursor = db.get_cursor(conn)
    updated = 0

    try:
        # Get all open signals
        db.db_execute(cursor, """
            SELECT id, symbol, entry_price, target_price, stop_loss, date_generated
            FROM signal_log WHERE outcome = 'open'
        """)
        rows = cursor.fetchall()

        for row in rows:
            sig_id = row[0] if isinstance(row, (list, tuple)) else row["id"]
            symbol = row[1] if isinstance(row, (list, tuple)) else row["symbol"]
            entry = row[2] if isinstance(row, (list, tuple)) else row["entry_price"]
            target = row[3] if isinstance(row, (list, tuple)) else row["target_price"]
            sl = row[4] if isinstance(row, (list, tuple)) else row["stop_loss"]
            date_gen = row[5] if isinstance(row, (list, tuple)) else row["date_generated"]

            if not entry or not target or not sl:
                continue

            try:
                ticker = f"{symbol}.NS"
                df = download_ohlcv(ticker, period="1mo", interval="1d")
                if df is None or df.empty:
                    continue

                # Get data after signal date
                actual_open = float(df["Open"].iloc[-1]) if len(df) > 0 else None
                actual_high = float(df["High"].iloc[-1]) if len(df) > 0 else None
                actual_low = float(df["Low"].iloc[-1]) if len(df) > 0 else None
                actual_close = float(df["Close"].iloc[-1]) if len(df) > 0 else None

                # Check outcome: did price hit target or stop loss first?
                outcome = "open"
                days_to_outcome = None

                # Look through recent price data
                for i in range(len(df)):
                    high = float(df["High"].iloc[i])
                    low = float(df["Low"].iloc[i])

                    if high >= target:
                        outcome = "hit_target"
                        days_to_outcome = i + 1
                        break
                    elif low <= sl:
                        outcome = "hit_sl"
                        days_to_outcome = i + 1
                        break

                # Update the record
                db.db_execute(cursor, """
                    UPDATE signal_log 
                    SET actual_open = ?, actual_high = ?, actual_low = ?, actual_close = ?,
                        outcome = ?, days_to_outcome = ?
                    WHERE id = ?
                """, (actual_open, actual_high, actual_low, actual_close,
                      outcome, days_to_outcome, sig_id))
                updated += 1

            except Exception as e:
                print(f"⚠️ Outcome check failed for {symbol}: {e}")

        conn.commit()
    except Exception as e:
        print(f"❌ Accuracy update error: {e}")
    finally:
        db.put_connection(conn)

    print(f"✅ Updated {updated} signal outcomes")
    return {"updated": updated}


def get_accuracy_stats():
    """Get accuracy statistics from signal log."""
    conn = db.get_connection()
    if not conn:
        return {"error": "No DB connection"}

    cursor = db.get_cursor(conn)
    stats = {}

    try:
        # Total signals
        db.db_execute(cursor, "SELECT COUNT(*) FROM signal_log")
        total = cursor.fetchone()[0]

        # Outcome breakdown
        db.db_execute(cursor, """
            SELECT outcome, COUNT(*) FROM signal_log GROUP BY outcome
        """)
        outcomes = {r[0]: r[1] for r in cursor.fetchall()}

        hit_target = outcomes.get("hit_target", 0)
        hit_sl = outcomes.get("hit_sl", 0)
        still_open = outcomes.get("open", 0)
        evaluated = hit_target + hit_sl

        win_rate = round((hit_target / evaluated) * 100, 1) if evaluated > 0 else 0

        # Average days to outcome
        db.db_execute(cursor, """
            SELECT AVG(days_to_outcome) FROM signal_log 
            WHERE outcome != 'open' AND days_to_outcome IS NOT NULL
        """)
        avg_days_row = cursor.fetchone()
        avg_days = round(float(avg_days_row[0]), 1) if avg_days_row and avg_days_row[0] else 0

        # By signal type
        db.db_execute(cursor, """
            SELECT signal_type, 
                   COUNT(*) as total,
                   SUM(CASE WHEN outcome = 'hit_target' THEN 1 ELSE 0 END) as wins
            FROM signal_log 
            WHERE outcome != 'open'
            GROUP BY signal_type
        """)
        by_signal = []
        for r in cursor.fetchall():
            sig_type = r[0]
            sig_total = r[1]
            sig_wins = r[2]
            by_signal.append({
                "signal": sig_type,
                "total": sig_total,
                "wins": sig_wins,
                "win_rate": round((sig_wins / sig_total) * 100, 1) if sig_total > 0 else 0,
            })

        # By segment
        db.db_execute(cursor, """
            SELECT segment,
                   COUNT(*) as total,
                   SUM(CASE WHEN outcome = 'hit_target' THEN 1 ELSE 0 END) as wins
            FROM signal_log
            WHERE outcome != 'open'
            GROUP BY segment
        """)
        by_segment = []
        for r in cursor.fetchall():
            by_segment.append({
                "segment": r[0],
                "total": r[1],
                "wins": r[2],
                "win_rate": round((r[2] / r[1]) * 100, 1) if r[1] > 0 else 0,
            })

        # Recent signals log (for transparency table)
        db.db_execute(cursor, """
            SELECT symbol, signal_type, score, entry_price, target_price, stop_loss,
                   outcome, days_to_outcome, segment, date_generated
            FROM signal_log ORDER BY date_generated DESC LIMIT 50
        """)
        recent = []
        for r in cursor.fetchall():
            recent.append({
                "symbol": r[0], "signal": r[1], "score": r[2],
                "entry": r[3], "target": r[4], "sl": r[5],
                "outcome": r[6], "days": r[7], "segment": r[8], "date": r[9],
            })

        # Average return for hit_target signals
        db.db_execute(cursor, """
            SELECT AVG((target_price - entry_price) / entry_price * 100)
            FROM signal_log WHERE outcome = 'hit_target' AND entry_price > 0
        """)
        avg_ret_row = cursor.fetchone()
        avg_return = round(float(avg_ret_row[0]), 2) if avg_ret_row and avg_ret_row[0] else 0

        stats = {
            "total_signals": total,
            "evaluated": evaluated,
            "hit_target": hit_target,
            "hit_sl": hit_sl,
            "still_open": still_open,
            "win_rate": win_rate,
            "avg_holding_days": avg_days,
            "avg_return": avg_return,
            "by_signal_type": by_signal,
            "by_segment": by_segment,
            "recent_signals": recent,
        }

    except Exception as e:
        print(f"❌ Accuracy stats error: {e}")
        stats = {"error": str(e)}
    finally:
        db.put_connection(conn)

    return stats
