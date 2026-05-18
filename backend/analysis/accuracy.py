"""
MarketPulse — Accuracy Analyser
Tracks signal outcomes and generates performance metrics.
Compares predicted signals with actual market outcomes.
"""
from datetime import datetime, timedelta
from data.stock_fetcher import download_ohlcv
import database as db


def resolve_pending_signals():
    """Check open signals and update outcomes based on actual price data.
    Run this daily after market close.
    """
    conn = db.get_connection()
    if not conn:
        return {"updated": 0, "error": "No DB connection"}

    cursor = db.get_cursor(conn)
    updated = 0

    try:
        # Get all pending signals from the last 5 days
        five_days_ago = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT id, symbol, entry_price, target_price, stop_loss, signal_type, date_generated 
            FROM signal_log 
            WHERE (outcome IS NULL OR outcome = 'open') AND date_generated >= %s
        """ if db.DATABASE_URL else """
            SELECT id, symbol, entry_price, target_price, stop_loss, signal_type, date_generated 
            FROM signal_log 
            WHERE (outcome IS NULL OR outcome = 'open') AND date_generated >= ?
        """, (five_days_ago,))
        rows = cursor.fetchall()
        
        for row in rows:
            sig_id = row[0] if isinstance(row, (list, tuple)) else row["id"]
            symbol = row[1] if isinstance(row, (list, tuple)) else row["symbol"]
            entry = row[2] if isinstance(row, (list, tuple)) else row["entry_price"]
            target = row[3] if isinstance(row, (list, tuple)) else row["target_price"]
            sl = row[4] if isinstance(row, (list, tuple)) else row["stop_loss"]
            signal_type = row[5] if isinstance(row, (list, tuple)) else row["signal_type"]
            
            if not entry or not target or not sl:
                continue
                
            try:
                from data.stock_fetcher import get_stock_data
                df = get_stock_data(symbol, period="5d", interval="1d")
                if not df or len(df) == 0:
                    continue
                    
                current_price = float(df[-1]["Close"])
                
                outcome = None
                actual_return_pct = 0.0
                if signal_type == "BUY":
                    actual_return_pct = ((current_price - entry) / entry) * 100
                    if current_price > entry:
                        outcome = "WIN"
                    elif current_price < sl:
                        outcome = "LOSS"
                elif signal_type == "SELL":
                    actual_return_pct = ((entry - current_price) / entry) * 100
                    if current_price < entry:
                        outcome = "WIN"
                    elif current_price > sl:
                        outcome = "LOSS"
                        
                if outcome:
                    cursor.execute("""
                        UPDATE signal_log 
                        SET outcome = ?
                        WHERE id = ?
                    """, (outcome, sig_id))
                    
                    # Phase 3: Also update prediction_log for Championship
                    try:
                        cursor.execute("""
                            UPDATE prediction_log
                            SET outcome = ?, resolved_date = ?, actual_return_pct = ?
                            WHERE symbol = ? AND signal_type = ? AND outcome IS NULL
                        """, (outcome, datetime.now().strftime('%Y-%m-%d'), round(actual_return_pct, 4), symbol, signal_type))
                        
                        # Trigger Alpha Decay Monitor & Calibrator
                        try:
                            from analysis.alpha_decay import AlphaDecayMonitor
                            from arena.calibrator import ConfidenceCalibrator
                            
                            models = ["technical", "transformer", "options_flow", "ml_engine", "sentiment", "insider", "macro", "momentum"]
                            decay = AlphaDecayMonitor(signal_names=models)
                            
                            # Parse model votes to update decay monitor
                            cursor.execute("SELECT model_votes_json, confidence FROM prediction_log WHERE symbol = ? AND signal_type = ? AND outcome = ?", (symbol, signal_type, outcome))
                            row = cursor.fetchone()
                            if row:
                                import json
                                votes = json.loads(row[0])
                                conf = row[1]
                                for m, vote in votes.items():
                                    if vote != 0:
                                        # If vote > 0 and outcome WIN -> 1. If vote < 0 and outcome LOSS -> 1. Else 0.
                                        is_correct = 1 if ((vote > 0 and outcome == 'WIN') or (vote < 0 and outcome == 'LOSS')) else 0
                                        decay.update(m, prediction=1, actual=is_correct)
                                        
                                # Update calibrator
                                calib = ConfidenceCalibrator()
                                calib.log_outcome(conf, outcome == 'WIN')
                                
                        except Exception as mon_ex:
                            print(f"Failed to update monitors: {mon_ex}")
                            
                    except Exception as ex:
                        print(f"Failed to update prediction_log: {ex}")
                        
                    updated += 1
            except Exception as e:
                print(f"Warning: Failed to resolve {symbol}: {e}")
                
        conn.commit()
    except Exception as e:
        print(f"❌ Error resolving signals: {e}")
    finally:
        db.put_connection(conn)
        
    print(f"✅ Resolved {updated} signal outcomes")
    return {"updated": updated}


def get_accuracy_stats():
    """Calculate historical accuracy of signals."""
    stats = {}

    try:
        # Total signals
        res = db.db_execute("SELECT COUNT(*) as count FROM signal_log")
        total = res[0]["count"] if res else 0

        # Outcome breakdown
        out_res = db.db_execute("SELECT outcome, COUNT(*) as count FROM signal_log GROUP BY outcome")
        outcomes = {r["outcome"]: r["count"] for r in (out_res or [])}

        wins = outcomes.get("WIN", 0)
        losses = outcomes.get("LOSS", 0)
        pending = outcomes.get(None, 0)
        evaluated = wins + losses

        win_rate = round((wins / evaluated) * 100, 1) if evaluated > 0 else 0

        # By signal type
        sig_res = db.db_execute("""
            SELECT signal_type, 
                   COUNT(*) as total,
                   SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins
            FROM signal_log 
            WHERE outcome IS NOT NULL
            GROUP BY signal_type
        """)
        by_signal = []
        for r in (sig_res or []):
            sig_total = r["total"]
            sig_wins = r["wins"]
            by_signal.append({
                "signal": r["signal_type"],
                "total": sig_total,
                "wins": sig_wins,
                "win_rate": round((sig_wins / sig_total) * 100, 1) if sig_total > 0 else 0,
            })

        # By regime
        regime_res = db.db_execute("""
            SELECT regime, 
                   COUNT(*) as total,
                   SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins
            FROM signal_log 
            WHERE outcome IS NOT NULL AND regime IS NOT NULL
            GROUP BY regime
        """)
        by_regime = []
        for r in (regime_res or []):
            reg_total = r["total"]
            reg_wins = r["wins"]
            by_regime.append({
                "regime": r["regime"],
                "total": reg_total,
                "wins": reg_wins,
                "win_rate": round((reg_wins / reg_total) * 100, 1) if reg_total > 0 else 0,
            })

        # Recent resolved signals (last 20)
        recent_res = db.db_execute("""
            SELECT symbol, signal_type, score, entry_price, target_price, 
                   stop_loss, outcome, timestamp
            FROM signal_log 
            WHERE outcome IS NOT NULL
            ORDER BY id DESC LIMIT 20
        """)
        recent_signals = []
        for r in (recent_res or []):
            recent_signals.append({
                "symbol": r["symbol"],
                "signal": r["signal_type"],
                "score": r["score"],
                "entry": r["entry_price"],
                "target": r["target_price"],
                "sl": r["stop_loss"],
                "outcome": r["outcome"],
                "date": r["timestamp"],
            })

        stats = {
            "total_signals": total,
            "wins": wins,
            "losses": losses,
            "pending": pending,
            "win_rate": win_rate,
            "by_signal": by_signal,
            "by_regime": by_regime,
            "recent_signals": recent_signals,
        }
        return stats

    except Exception as e:
        print(f"❌ Accuracy stats error: {e}")
        stats = {"error": str(e)}

    return stats

def verify_intraday_predictions():
    """Check pending intraday predictions against actual market data."""
    try:
        # Get pending predictions where target_date <= today
        today = datetime.now().strftime("%Y-%m-%d")
        rows = db.db_execute(f"SELECT * FROM daily_predictions WHERE status = 'pending' AND target_date <= '{today}'")
        
        if not rows: return
        
        updated = 0
        for row in rows:
            pid = row["id"]
            sym = row["symbol"]
            t_date = row["target_date"]
            p_high = row["pred_high"]
            p_low = row["pred_low"]
            p_dir = row["pred_direction"]
            
            ticker = f"{sym}.NS"
            df = download_ohlcv(ticker, period="5d", interval="1d")
            if df is None or df.empty: continue
            
            # Find the row corresponding to target_date
            # yfinance index is DatetimeIndex
            df_target = df[df.index.strftime('%Y-%m-%d') == t_date]
            
            if df_target.empty:
                continue # Data not yet available for this date
                
            actual_open = float(df_target["Open"].iloc[0])
            actual_high = float(df_target["High"].iloc[0])
            actual_low = float(df_target["Low"].iloc[0])
            actual_close = float(df_target["Close"].iloc[0])
            
            # Determine status
            status_parts = []
            if actual_high <= p_high and actual_low >= p_low:
                status_parts.append("✅ Within Range")
            else:
                status_parts.append("❌ Range Breached")
                
            actual_dir = "Bullish" if actual_close > actual_open else "Bearish" if actual_close < actual_open else "Neutral"
            if p_dir == actual_dir:
                status_parts.append("✅ Direction Hit")
            else:
                status_parts.append("❌ Direction Missed")
                
            final_status = " | ".join(status_parts)
            
            db.db_execute("""
                UPDATE daily_predictions 
                SET actual_open=?, actual_high=?, actual_low=?, actual_close=?, status=?
                WHERE id=?
            """, (actual_open, actual_high, actual_low, actual_close, final_status, pid))
            updated += 1
            
        print(f"✅ Verified {updated} intraday predictions")
    except Exception as e:
        print(f"❌ Failed to verify intraday predictions: {e}")
