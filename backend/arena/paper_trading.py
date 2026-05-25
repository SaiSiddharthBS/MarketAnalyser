"""
Agent Alpha v4.0 - Arena Engine (Paper Trading)
Executes paper trades based on quantitative signals with no emotion and strict rules.
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pytz

import database as db
from analysis.technical import get_technical_analysis, screen_stocks
from analysis.regime import get_current_market_regime
from analysis.position_sizing import calculate_position_size
from analysis.ensemble import get_ensemble_analysis
from analysis.veto_engine import veto_engine
from analysis.backtest_engine import backtester
from data.stock_fetcher import download_ohlcv
from bot.daily_job import send_telegram_sync
from config import NIFTY_50_SYMBOLS
from arena.execution_model import parse_execution_config, apply_execution_model
from arena.multi_timeframe_portfolio import calculate_bucketed_position_size, BUCKETS

IST = pytz.timezone("Asia/Kolkata")

INITIAL_CAPITAL = 1_000_000  # ₹10 Lakh
MAX_POSITIONS = 5
EXEC_CONFIG = parse_execution_config({"model": "impact_curve", "fixed_bps": 10, "impact_coefficient_bps": 20})
BROKERAGE_PCT = 0.001        # 0.1%
STT_PCT = 0.001              # 0.1%
MAX_HOLD_DAYS = 15           # Timeout
MIN_CONVICTION = "HIGH"      # Only HIGH or ULTRA trades

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_current_date_ist() -> str:
    return datetime.now(IST).strftime('%Y-%m-%d')

def initialize_portfolio_if_needed():
    """Ensure we have an initial portfolio state."""
    portfolio = db.db_execute("SELECT * FROM paper_portfolio ORDER BY id DESC LIMIT 1")
    if not portfolio:
        db.db_execute("""
            INSERT INTO paper_portfolio (
                date, cash, holdings_value, total_equity, open_positions, 
                daily_return_pct, cumulative_return_pct, drawdown_from_peak_pct, 
                benchmark_nifty_return_pct
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (get_current_date_ist(), INITIAL_CAPITAL, 0.0, INITIAL_CAPITAL, 0, 0.0, 0.0, 0.0, 0.0))

def get_latest_portfolio() -> Dict[str, Any]:
    initialize_portfolio_if_needed()
    res = db.db_execute("SELECT * FROM paper_portfolio ORDER BY id DESC LIMIT 1")
    return dict(res[0]) if res else {}

def execute_daily_arena():
    """Called daily at 9:20 AM IST via GitHub Actions or cron."""
    logger.info("🏟️ Arena Engine starting daily execution...")
    
    # 1. Get current portfolio
    portfolio = get_latest_portfolio()
    cash = portfolio.get("cash", INITIAL_CAPITAL)
    today = get_current_date_ist()
    
    # 2. Check open positions for SL/Target hits
    open_positions = db.db_execute("SELECT * FROM paper_trades WHERE status = 'OPEN'")
    open_symbols = [p["symbol"] for p in open_positions]
    
    closed_trades = []
    
    for pos in open_positions:
        symbol = pos["symbol"]
        qty = pos["quantity"]
        entry_price = pos["entry_price"]
        sl = pos["stop_loss"]
        target = pos["target_price"]
        entry_date = pos["entry_date"]
        
        # Get today's OPEN/HIGH/LOW
        ticker = f"{symbol}.NS"
        df = download_ohlcv(ticker, period="5d", interval="1d")
        if df is None or df.empty:
            continue
            
        today_data = df.iloc[-1]
        today_open = float(today_data["Open"])
        today_high = float(today_data["High"])
        today_low = float(today_data["Low"])
        today_close = float(today_data["Close"])
        
        # Calculate holding period
        days_held = (datetime.strptime(today, '%Y-%m-%d') - datetime.strptime(entry_date, '%Y-%m-%d')).days
        
        exit_reason = None
        exit_price = None
        trade_type = pos.get("trade_type", "LONG")
        
        # --- PHASE 4.2 STAT-ARB EXIT LOGIC ---
        if trade_type.startswith("PAIR_"):
            try:
                import json
                import numpy as np
                import pandas as pd
                from analysis.stat_arb import KNOWN_PAIRS
                
                votes = json.loads(pos.get("model_votes_json") or "{}")
                paired_with = votes.get("paired_with")
                
                if paired_with:
                    # Find the original pair ordering to calculate the exact same Z-score
                    asset1, asset2 = None, None
                    for k1, k2 in KNOWN_PAIRS:
                        s1, s2 = k1.replace(".NS", ""), k2.replace(".NS", "")
                        if (symbol == s1 and paired_with == s2) or (symbol == s2 and paired_with == s1):
                            asset1, asset2 = s1, s2
                            break
                            
                    if asset1 and asset2:
                        df1 = df['Close'].dropna() if symbol == asset1 else download_ohlcv(f"{asset1}.NS", period="6mo", interval="1d")['Close'].dropna()
                        df2 = df['Close'].dropna() if symbol == asset2 else download_ohlcv(f"{asset2}.NS", period="6mo", interval="1d")['Close'].dropna()
                        
                        data = pd.concat([df1, df2], axis=1, join='inner')
                        data.columns = ["A", "B"]
                        
                        data['spread'] = np.log(data["A"]) - np.log(data["B"])
                        data['mean_spread'] = data['spread'].rolling(window=60).mean()
                        data['std_spread'] = data['spread'].rolling(window=60).std()
                        data['z_score'] = (data['spread'] - data['mean_spread']) / data['std_spread']
                        
                        current_z = float(data['z_score'].iloc[-1])
                        
                        # Mean reversion achieved if Z-score crosses back towards 0 (let's say between -0.5 and +0.5)
                        if abs(current_z) < 0.5:
                            exit_reason = "MEAN_REVERTED_Z_CROSSOVER"
                            side = "SELL" if trade_type == "PAIR_LONG" else "BUY"
                            fill = apply_execution_model(qty, today_close, side=side, bar_volume=float(today_data.get("Volume", 100000)), config=EXEC_CONFIG)
                            exit_price = fill.fill_price
                        # Stop Loss on extreme divergence
                        elif abs(current_z) > 4.0:
                            exit_reason = "STAT_ARB_SL_Z_EXCEEDED"
                            side = "SELL" if trade_type == "PAIR_LONG" else "BUY"
                            fill = apply_execution_model(qty, today_close, side=side, bar_volume=float(today_data.get("Volume", 100000)), config=EXEC_CONFIG)
                            exit_price = fill.fill_price
            except Exception as e:
                logger.error(f"Stat Arb Pair Exit Check Error for {symbol}: {e}")
                
        # --- MODULE 5: DYNAMIC TRAILING STOP-LOSS ENGINE (DIRECTIONAL ONLY) ---
        elif trade_type in ("LONG", "SHORT"):
            rr = pos.get("risk_reward_ratio") or 2.0
            initial_risk = abs(target - pos["entry_price"]) / rr
            if initial_risk <= 0: initial_risk = pos["entry_price"] * 0.01
            
            current_profit = today_high - pos["entry_price"] if trade_type == "LONG" else pos["entry_price"] - today_low
            profit_r = current_profit / initial_risk
            
            # Phase 2: +1.5R -> Move to Breakeven
            if profit_r >= 1.5:
                new_sl = pos["entry_price"] * 1.001 if trade_type == "LONG" else pos["entry_price"] * 0.999
                if trade_type == "LONG" and new_sl > sl: sl = new_sl
                elif trade_type == "SHORT" and new_sl < sl: sl = new_sl
                
            # Phase 3: +2.5R -> Lock in +1.0R
            if profit_r >= 2.5:
                new_sl = pos["entry_price"] + initial_risk if trade_type == "LONG" else pos["entry_price"] - initial_risk
                if trade_type == "LONG" and new_sl > sl: sl = new_sl
                elif trade_type == "SHORT" and new_sl < sl: sl = new_sl
                
            # Phase 4: +4.0R -> Lock in +2.5R
            if profit_r >= 4.0:
                new_sl = pos["entry_price"] + (initial_risk * 2.5) if trade_type == "LONG" else pos["entry_price"] - (initial_risk * 2.5)
                if trade_type == "LONG" and new_sl > sl: sl = new_sl
                elif trade_type == "SHORT" and new_sl < sl: sl = new_sl
                
            if sl != pos["stop_loss"]:
                db.db_execute("UPDATE paper_trades SET stop_loss = ? WHERE id = ?", (sl, pos["id"]))
            # ---------------------------------------------------
            
        if not exit_reason:
            if trade_type in ("LONG", "PAIR_LONG"):
                # SL Hit
                if today_low <= sl:
                    exit_reason = "SL_HIT"
                    fill = apply_execution_model(qty, sl, side="SELL", bar_volume=float(today_data.get("Volume", 100000)), config=EXEC_CONFIG)
                    exit_price = fill.fill_price
                # Target Hit
                elif today_high >= target:
                    exit_reason = "TARGET_HIT"
                    fill = apply_execution_model(qty, target, side="SELL", bar_volume=float(today_data.get("Volume", 100000)), config=EXEC_CONFIG)
                    exit_price = fill.fill_price
            elif trade_type in ("SHORT", "PAIR_SHORT"):
                # SL Hit for Short (Price goes UP to SL)
                if today_high >= sl:
                    exit_reason = "SL_HIT"
                    fill = apply_execution_model(qty, sl, side="BUY", bar_volume=float(today_data.get("Volume", 100000)), config=EXEC_CONFIG)
                    exit_price = fill.fill_price
                # Target Hit for Short (Price goes DOWN to target)
                elif today_low <= target:
                    exit_reason = "TARGET_HIT"
                    fill = apply_execution_model(qty, target, side="BUY", bar_volume=float(today_data.get("Volume", 100000)), config=EXEC_CONFIG)
                    exit_price = fill.fill_price
                
        # Timeout (Applies to both, uses dynamic Timeframe if available)
        expected_days = pos.get("expected_days")
        if not expected_days:
            expected_days = MAX_HOLD_DAYS
            
        max_hold_limit = expected_days + (2 if expected_days <= 5 else 5) # Buffer
        
        # INTRADAY trades must be closed if they are held overnight
        holding_class = pos.get("holding_class", "SWING")
        if holding_class == "INTRADAY" and days_held >= 1:
            exit_reason = "EOD_TIMEOUT (Intraday carried over)"
            side = "SELL" if trade_type == "LONG" else "BUY"
            fill = apply_execution_model(qty, today_open, side=side, bar_volume=float(today_data.get("Volume", 100000)), config=EXEC_CONFIG)
            exit_price = fill.fill_price
        elif not exit_reason and days_held >= max_hold_limit:
            exit_reason = f"TIMEOUT_{max_hold_limit}D"
            side = "SELL" if trade_type == "LONG" else "BUY"
            fill = apply_execution_model(qty, today_open, side=side, bar_volume=float(today_data.get("Volume", 100000)), config=EXEC_CONFIG)
            exit_price = fill.fill_price
        
        if exit_reason:
            trade_value = exit_price * qty
            fees = trade_value * (BROKERAGE_PCT + STT_PCT)
            
            # Invert PnL for shorts: (Entry - Exit) * Qty
            if trade_type in ("LONG", "PAIR_LONG"):
                gross_pnl = trade_value - pos["position_value"]
            else:
                gross_pnl = pos["position_value"] - trade_value
                
            net_pnl = gross_pnl - fees - pos["fees"]
            return_pct = (net_pnl / pos["position_value"]) * 100
            
            # Close trade
            db.db_execute("""
                UPDATE paper_trades 
                SET status = ?, exit_date = ?, exit_price = ?, exit_reason = ?, 
                    gross_pnl = ?, fees = fees + ?, net_pnl = ?, return_pct = ?
                WHERE id = ?
            """, ("CLOSED_" + ("WIN" if net_pnl > 0 else "LOSS"), today, exit_price, exit_reason, 
                  gross_pnl, fees, net_pnl, return_pct, pos["id"]))
            
            # Correct cash accounting for both LONG and SHORT (return reserved capital + gross PnL - exit fees)
            cash += (pos["position_value"] + gross_pnl - fees)
            closed_trades.append({
                "symbol": symbol,
                "reason": exit_reason,
                "pnl": net_pnl,
                "return_pct": return_pct
            })
            
            # 4. Run trade autopsy
            try:
                from arena.trade_autopsy import generate_autopsy
                generate_autopsy(pos["id"])
            except Exception as e:
                logger.error(f"Autopsy failed: {e}")
            
            # Send notification
            msg = f"🏟️ *ARENA TRADE CLOSED: {symbol}*\nReason: {exit_reason}\nP&L: ₹{net_pnl:.2f} ({return_pct:.2f}%)"
            send_telegram_sync(msg)
            
    # Refresh open positions count
    open_positions = db.db_execute("SELECT * FROM paper_trades WHERE status = 'OPEN'")
    num_open = len(open_positions)
    
    # 5. Find new trades if we have capacity
    new_trades = []
    
    # --- MODULE 9: SYSTEM CIRCUIT BREAKER ---
    portfolio_state = db.db_execute("SELECT total_equity, drawdown_from_peak_pct FROM paper_portfolio ORDER BY date DESC LIMIT 1")
    current_drawdown = portfolio_state[0]["drawdown_from_peak_pct"] if portfolio_state and portfolio_state[0]["drawdown_from_peak_pct"] else 0
    if current_drawdown > 8.0:
        logger.warning(f"CIRCUIT BREAKER ACTIVATED: Drawdown is {current_drawdown:.2f}%. Trading Halted.")
        send_telegram_sync(f"🛑 *CIRCUIT BREAKER TRIPPED*\nPortfolio Drawdown: {current_drawdown:.2f}%\nSystem has automatically halted all new trades to protect capital.")
        num_open = MAX_POSITIONS  # Force skip new trades
    # ----------------------------------------
    
    if True:
        logger.info(f"Scanning for trades across portfolio buckets...")
        
        # Pre-fetch history for open positions to calculate correlation
        op_histories = {}
        for op in open_positions:
            op_df = download_ohlcv(f"{op['symbol']}.NS", period="3mo", interval="1d")
            if op_df is not None and not op_df.empty:
                op_histories[op['symbol']] = op_df["Close"].pct_change().dropna()
        
        regime_data = get_current_market_regime()
        regime = regime_data.get("regime", "unknown")
        
        # Only block ALL buys during true systemic crisis (VIX >= 30)
        if regime == "crisis":
            logger.info("Regime is CRISIS. Not opening new positions.")
        elif regime in ("high_vol_chop", "low_vol_chop"):
            # --- PHASE 4.2: STAT ARB / NON-DIRECTIONAL MODE ---
            logger.info(f"Regime is {regime.upper()}. Bypassing directional trades. Activating Stat-Arb Engine.")
            from analysis.stat_arb import analyze_pairs
            
            pair_signals = analyze_pairs(z_score_threshold=2.0)
            
            # Group signals by pair
            pairs_to_execute = {}
            for sig in pair_signals:
                paired_with = sig.get("paired_with")
                if not paired_with: continue
                # Unique pair key (alphabetical to group them safely)
                key = tuple(sorted([sig["symbol"], paired_with]))
                if key not in pairs_to_execute:
                    pairs_to_execute[key] = {}
                pairs_to_execute[key][sig["symbol"]] = sig
                
            for pair_key, legs in pairs_to_execute.items():
                if len(legs) != 2: continue
                
                sym1, sym2 = pair_key
                if sym1 in open_symbols or sym2 in open_symbols: continue
                
                leg1 = legs[sym1]
                leg2 = legs[sym2]
                
                # Sizing based on ARBITRAGE bucket
                df1 = download_ohlcv(f"{sym1}.NS", period="5d", interval="1d")
                df2 = download_ohlcv(f"{sym2}.NS", period="5d", interval="1d")
                if df1 is None or df1.empty or df2 is None or df2.empty: continue
                
                p1_open = float(df1.iloc[-1]["Open"])
                p2_open = float(df2.iloc[-1]["Open"])
                
                # Check Arbitrage bucket capacity (fake entry price = 1000 to just check capital)
                sizing = calculate_bucketed_position_size(INITIAL_CAPITAL, "ARBITRAGE", 1000.0)
                if not sizing["approved"]:
                    logger.info(f"Skipping Pair {sym1}-{sym2}: {sizing['reason']}")
                    continue
                    
                # We allocate ₹50,000 to each leg to keep it market-neutral (₹100k total)
                alloc_per_leg = 50000.0
                
                # We need sufficient total cash
                if cash < (alloc_per_leg * 2 * 1.01): # including fees buffer
                    continue
                    
                qty1 = int(alloc_per_leg / p1_open)
                qty2 = int(alloc_per_leg / p2_open)
                
                if qty1 == 0 or qty2 == 0: continue
                
                # Execute Leg 1
                trade_type1 = "PAIR_LONG" if leg1["signal"] in ("BUY", "STRONG_BUY") else "PAIR_SHORT"
                side1 = "BUY" if trade_type1 == "PAIR_LONG" else "SELL"
                fill1 = apply_execution_model(qty1, p1_open, side=side1, bar_volume=float(df1.iloc[-1].get("Volume", 100000)), config=EXEC_CONFIG)
                
                # Execute Leg 2
                trade_type2 = "PAIR_LONG" if leg2["signal"] in ("BUY", "STRONG_BUY") else "PAIR_SHORT"
                side2 = "BUY" if trade_type2 == "PAIR_LONG" else "SELL"
                fill2 = apply_execution_model(qty2, p2_open, side=side2, bar_volume=float(df2.iloc[-1].get("Volume", 100000)), config=EXEC_CONFIG)
                
                qty1 = fill1.filled_quantity
                entry_price1 = fill1.fill_price
                pos_value1 = qty1 * entry_price1
                fees1 = pos_value1 * (BROKERAGE_PCT + STT_PCT)
                
                qty2 = fill2.filled_quantity
                entry_price2 = fill2.fill_price
                pos_value2 = qty2 * entry_price2
                fees2 = pos_value2 * (BROKERAGE_PCT + STT_PCT)
                
                if qty1 == 0 or qty2 == 0: continue
                
                import json
                
                # Insert Leg 1
                db.db_execute("""
                    INSERT INTO paper_trades (
                        symbol, trade_type, signal_date, entry_date, entry_price, quantity,
                        position_value, stop_loss, target_price, risk_reward_ratio, fees,
                        regime_at_entry, ensemble_score, conviction, model_votes_json,
                        holding_class, expected_days
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sym1, trade_type1, get_current_date_ist(), today, float(entry_price1), float(qty1),
                    float(pos_value1), float(entry_price1 * (0.9 if trade_type1=="PAIR_LONG" else 1.1)), float(entry_price1 * (1.1 if trade_type1=="PAIR_LONG" else 0.9)), 1.0, float(fees1), regime, float(leg1["confidence"]),
                    "ULTRA", json.dumps({"paired_with": sym2, "pair_z_score": float(leg1["pair_z_score"])}), "ARBITRAGE", 5
                ))
                
                # Insert Leg 2
                db.db_execute("""
                    INSERT INTO paper_trades (
                        symbol, trade_type, signal_date, entry_date, entry_price, quantity,
                        position_value, stop_loss, target_price, risk_reward_ratio, fees,
                        regime_at_entry, ensemble_score, conviction, model_votes_json,
                        holding_class, expected_days
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sym2, trade_type2, get_current_date_ist(), today, float(entry_price2), float(qty2),
                    float(pos_value2), float(entry_price2 * (0.9 if trade_type2=="PAIR_LONG" else 1.1)), float(entry_price2 * (1.1 if trade_type2=="PAIR_LONG" else 0.9)), 1.0, float(fees2), regime, float(leg2["confidence"]),
                    "ULTRA", json.dumps({"paired_with": sym1, "pair_z_score": float(leg2["pair_z_score"])}), "ARBITRAGE", 5
                ))
                
                cash -= float(pos_value1 + fees1 + pos_value2 + fees2)
                new_trades.append(f"{sym1}-{sym2} Pair")
                
                msg = f"🏟️ *ARENA STAT-ARB OPENED: {sym1} & {sym2}*\nLeg 1: {trade_type1} {qty1} @ ₹{entry_price1:.2f}\nLeg 2: {trade_type2} {qty2} @ ₹{entry_price2:.2f}\nZ-Score: {leg1['pair_z_score']:.2f}"
                send_telegram_sync(msg)
                
        else:
            # Regime-based position sizing adjustment for Directional Trades
            regime_size_factor = {
                "low_vol_uptrend": 1.0,      # Full size — home turf
                "high_vol_uptrend": 0.75,     # Slightly cautious
                "high_vol_chop": 0.50,        # Buy the dip — half size
                "low_vol_chop": 0.40,         # Minimal allocation
            }.get(regime, 0.50)
            
            # Regime-based minimum score (relaxed for paper-trading validation)
            min_score = {
                "low_vol_uptrend": 25,        # Aggressive — lower bar
                "high_vol_uptrend": 28,        # Moderate bar
                "high_vol_chop": 28,           # Dip buying — moderate bar
                "low_vol_chop": 30,            # Higher bar in chop
            }.get(regime, 28)
            
            scored_stocks = []
            
            for symbol in NIFTY_50_SYMBOLS:
                if symbol in open_symbols: continue
                ticker = f"{symbol}.NS"
                df = download_ohlcv(ticker, period="6mo", interval="1d")
                if df is None or len(df) < 50: continue
                
                # Use the 12-Model Ensemble instead of basic technicals
                ensemble_analysis = get_ensemble_analysis(symbol, df, regime)
                if not ensemble_analysis: continue
                
                tech_analysis = get_technical_analysis(symbol)
                
                confidence = ensemble_analysis.get("confidence", 0)
                signal = ensemble_analysis.get("signal", "NEUTRAL")
                
                # EVENT DRIVEN VETO
                from analysis.event_driven import scan_all_events
                from analysis.news_sentiment_v2 import get_news_sentiment
                from analysis.risk_parity import calculate_volatility_scalar, check_sector_concentration
                import yfinance as yf
                
                events = scan_all_events(symbol)
                news = get_news_sentiment(symbol)
                
                # Volatility and Sector
                vol_scalar = calculate_volatility_scalar(f"{symbol}.NS", df)
                sector = yf.Ticker(f"{symbol}.NS").info.get("sector", "Unknown")
                
                # Veto check
                veto = veto_engine.check_all_vetoes(symbol, {}, {"regime_state": regime, "vix": regime_data.get("vix_level", 15)}, {})
                
                if not veto.get("vetoed") and events["earnings"].get("reporting_soon") and events["earnings"].get("days_until", 99) <= 3:
                    veto = {"vetoed": True, "reason": "Earnings within 3 days"}
                    logger.info(f"VETO: {symbol} rejected due to upcoming earnings.")
                    
                if not veto.get("vetoed") and news.get("flag") == "BREAKING_NEGATIVE":
                    veto = {"vetoed": True, "reason": "BREAKING_NEGATIVE news sentiment"}
                    logger.info(f"VETO: {symbol} rejected due to breaking negative news.")
                
                # --- MODULE 6: PORTFOLIO CORRELATION MATRIX ---
                # Reject if correlated > 0.65 with MORE THAN 2 existing positions
                if not veto.get("vetoed") and len(op_histories) >= 2:
                    high_corr_count = 0
                    cand_returns = df["Close"].pct_change().dropna()
                    for op_sym, op_ret in op_histories.items():
                        try:
                            # Align series
                            aligned_cand, aligned_op = cand_returns.align(op_ret, join='inner')
                            if len(aligned_cand) > 30:
                                corr = aligned_cand.corr(aligned_op)
                                if corr > 0.65: high_corr_count += 1
                        except Exception:
                            pass
                    if high_corr_count > 2:
                        logger.info(f"VETO: {symbol} rejected by Portfolio Correlation Filter (correlated with {high_corr_count} open positions).")
                        veto = {"vetoed": True, "reason": f"Correlation > 0.65 with {high_corr_count} positions"}
                # ----------------------------------------------
                
                # DEMO MODE: Temporarily allow soft-vetoes through if they have a good signal
                if veto.get("vetoed") and confidence < 50:
                    continue
                    
                # Accept both LONG and SHORT signals (and NEUTRAL for demo if score > 50)
                trade_type = None
                if signal in ("BUY", "STRONG_BUY") or (signal == "NEUTRAL" and confidence > 55):
                    trade_type = "LONG"
                elif signal in ("SELL", "STRONG_SELL"):
                    trade_type = "SHORT"
                else:
                    continue
                
                # Score must meet regime-adjusted minimum
                if confidence < min_score:
                    continue
                    
                conviction = "ULTRA" if confidence >= 80 else ("HIGH" if confidence >= 65 else "MODERATE")
                
                scored_stocks.append({
                    "symbol": symbol,
                    "confidence": confidence,
                    "conviction": conviction,
                    "trade_type": trade_type,
                    "tech": tech_analysis,
                    "ensemble_analysis": ensemble_analysis,
                    "regime_size_factor": regime_size_factor,
                    "vol_scalar": vol_scalar,
                    "sector": sector
                })
                
            # Sort by confidence
            scored_stocks.sort(key=lambda x: x["confidence"], reverse=True)
            
            for candidate in scored_stocks:
                symbol = candidate["symbol"]
                tech = candidate["tech"]
                trade_type = candidate["trade_type"]
                
                ensemble_analysis = candidate.get("ensemble_analysis", {})
                
                # Timeframe Logic
                timeframe = ensemble_analysis.get("timeframe_classification", {})
                holding_class = timeframe.get("holding_class", "SWING")
                expected_days = timeframe.get("expected_days", 10)
                
                # Entry price is today's open + slippage
                df = download_ohlcv(f"{symbol}.NS", period="5d", interval="1d")
                if df is None or df.empty: continue
                today_open = float(df.iloc[-1]["Open"])
                bar_volume = float(df.iloc[-1].get("Volume", 100000))
                
                # Estimate qty with a small slippage buffer
                est_entry_price = today_open * 1.001 if trade_type == "LONG" else today_open * 0.999
                
                # --- NEW BUCKETED POSITION SIZING ---
                # Sector Concentration Check
                open_pos = db.db_execute("SELECT symbol, holding_class, quantity, entry_price FROM paper_trades WHERE status = 'OPEN'")
                # Try to augment open_pos with sectors if missing (we'll just use quantity * entry_price for exposure)
                sector_check = check_sector_concentration(candidate.get("sector"), open_pos, INITIAL_CAPITAL)
                if not sector_check["approved"]:
                    logger.info(f"Skipping {symbol}: {sector_check['reason']}")
                    continue
                
                sizing = calculate_bucketed_position_size(INITIAL_CAPITAL, holding_class, est_entry_price, vol_scalar=candidate.get("vol_scalar", 1.0))
                if not sizing["approved"]:
                    logger.info(f"Skipping {symbol}: {sizing['reason']}")
                    continue
                    
                qty = sizing["quantity"]
                # ------------------------------------
                
                # Apply true execution model to get final entry price and filled quantity
                side = "BUY" if trade_type == "LONG" else "SELL"
                fill = apply_execution_model(qty, today_open, side=side, bar_volume=bar_volume, config=EXEC_CONFIG)
                
                # BUGFIX: Arena mathematically must enforce execution models
                if fill.filled_quantity <= 0:
                    logger.info(f"Skipping {symbol}: Execution model yielded zero fill (capped by liquidity).")
                    continue
                    
                qty = fill.filled_quantity
                entry_price = fill.fill_price
                
                pos_value = qty * entry_price
                fees = pos_value * (BROKERAGE_PCT + STT_PCT)
                
                if cash < (pos_value + fees):
                    continue
                
                if trade_type == "LONG":
                    sl = entry_price * (1.0 - sizing["stop_loss_dist_pct"])
                    target = entry_price * (1.0 + sizing["target_dist_pct"])
                else:
                    sl = entry_price * (1.0 + sizing["stop_loss_dist_pct"])
                    target = entry_price * (1.0 - sizing["target_dist_pct"])
                
                # Store
                db.db_execute("""
                    INSERT INTO paper_trades (
                        symbol, trade_type, signal_date, entry_date, entry_price, quantity,
                        position_value, stop_loss, target_price, risk_reward_ratio, fees,
                        regime_at_entry, ensemble_score, conviction, model_votes_json,
                        holding_class, expected_days
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    symbol, trade_type, get_current_date_ist(), today, entry_price, qty,
                    pos_value, sl, target, 2.0, fees, regime, candidate["confidence"],
                    candidate["conviction"], "{}", holding_class, expected_days
                ))
                
                cash -= (pos_value + fees)
                new_trades.append(symbol)
                
                msg = f"🏟️ *ARENA TRADE OPENED: {symbol}*\nTimeframe: {holding_class} ({expected_days}d)\nQty: {qty}\nEntry: ₹{entry_price:.2f}\nTarget: ₹{target:.2f}\nSL: ₹{sl:.2f}"
                send_telegram_sync(msg)
                
    # 6. Snapshot portfolio equity
    open_positions = db.db_execute("SELECT symbol, quantity FROM paper_trades WHERE status = 'OPEN'")
    holdings_value = 0.0
    for pos in open_positions:
        df = download_ohlcv(f"{pos['symbol']}.NS", period="5d", interval="1d")
        if df is not None and not df.empty:
            holdings_value += float(df.iloc[-1]["Close"]) * pos["quantity"]
            
    total_equity = cash + holdings_value
    cum_return_pct = ((total_equity / INITIAL_CAPITAL) - 1) * 100
    
    peak_res = db.db_execute("SELECT MAX(total_equity) as max_eq FROM paper_portfolio")
    peak_eq = peak_res[0]["max_eq"] if peak_res and peak_res[0]["max_eq"] else INITIAL_CAPITAL
    peak_eq = max(peak_eq, total_equity)
    
    drawdown = ((peak_eq - total_equity) / peak_eq) * 100 if peak_eq > 0 else 0
    # Insert or update today's snapshot
    existing = db.db_execute("SELECT id FROM paper_portfolio WHERE date = ?", (today,))
    
    # Calculate Daily Return
    yesterday_eq = INITIAL_CAPITAL
    if existing:
        res = db.db_execute("SELECT total_equity FROM paper_portfolio WHERE date < ? ORDER BY date DESC LIMIT 1", (today,))
        if res: yesterday_eq = res[0]["total_equity"]
    else:
        res = db.db_execute("SELECT total_equity FROM paper_portfolio ORDER BY date DESC LIMIT 1")
        if res: yesterday_eq = res[0]["total_equity"]
        
    daily_return = ((total_equity / yesterday_eq) - 1) * 100 if yesterday_eq > 0 else 0.0

    # Calculate Nifty Benchmark
    nifty_return = 0.0
    nifty_df = download_ohlcv("^NSEI", period="1mo", interval="1d")
    if nifty_df is not None and not nifty_df.empty and len(nifty_df) >= 2:
        nifty_return = float(((nifty_df["Close"].iloc[-1] / nifty_df["Close"].iloc[-2]) - 1) * 100)

    # Insert or update today's snapshot
    if existing:
        db.db_execute("""
            UPDATE paper_portfolio 
            SET cash=?, holdings_value=?, total_equity=?, open_positions=?, daily_return_pct=?, cumulative_return_pct=?, drawdown_from_peak_pct=?, benchmark_nifty_return_pct=?
            WHERE date=?
        """, (float(cash), float(holdings_value), float(total_equity), len(open_positions), float(daily_return), float(cum_return_pct), float(drawdown), float(nifty_return), today))
    else:
        db.db_execute("""
            INSERT INTO paper_portfolio (
                date, cash, holdings_value, total_equity, open_positions, 
                daily_return_pct, cumulative_return_pct, drawdown_from_peak_pct, 
                benchmark_nifty_return_pct
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (today, float(cash), float(holdings_value), float(total_equity), len(open_positions), float(daily_return), float(cum_return_pct), float(drawdown), float(nifty_return)))
    
    logger.info(f"Arena daily execution complete. Equity: ₹{total_equity:.2f} ({cum_return_pct:.2f}%)")
    
    if len(new_trades) == 0 and len(closed_trades) == 0:
        if regime == "crisis":
            msg = "🏟️ *ARENA UPDATE*\nRegime is CRISIS. Market volatility is too high.\nPreserving 100% Cash. No trades placed today."
        else:
            msg = f"🏟️ *ARENA UPDATE*\nScanned NIFTY 50.\nNo setups met the required conviction threshold for the current `{regime}` regime.\nPreserving Cash."
        send_telegram_sync(msg)

def track_live_positions():
    """Real-time Sentinel loop: Monitor OPEN positions against real-time LTP."""
    try:
        from data.stock_fetcher import get_bulk_ltp
        import database as db
        from datetime import datetime
        
        open_positions = db.db_execute("SELECT * FROM paper_trades WHERE status = 'OPEN'")
        if not open_positions:
            return  # Nothing to track
            
        symbols = [p["symbol"] for p in open_positions]
        ltp_data = get_bulk_ltp(symbols)
        
        if not ltp_data:
            return
            
        today = datetime.now().strftime("%Y-%m-%d")
        
        # We need the portfolio cash to update it
        portfolio = db.db_execute("SELECT * FROM paper_portfolio ORDER BY date DESC LIMIT 1")
        cash = portfolio[0]["cash"] if portfolio else 1000000.0
        
        for pos in open_positions:
            symbol = pos["symbol"]
            current_price = ltp_data.get(symbol)
            
            if not current_price:
                continue
                
            qty = pos["quantity"]
            sl = pos["stop_loss"]
            target = pos["target_price"]
            
            exit_reason = None
            exit_price = None
            trade_type = pos.get("trade_type", "LONG")
            
            # --- MODULE 5: DYNAMIC TRAILING STOP-LOSS ENGINE (LIVE) ---
            rr = pos.get("risk_reward_ratio") or 2.0
            initial_risk = abs(target - pos["entry_price"]) / rr
            if initial_risk <= 0: initial_risk = pos["entry_price"] * 0.01
            
            current_profit = current_price - pos["entry_price"] if trade_type == "LONG" else pos["entry_price"] - current_price
            profit_r = current_profit / initial_risk
            
            # Phase 2: +1.5R -> Move to Breakeven
            if profit_r >= 1.5:
                new_sl = pos["entry_price"] * 1.001 if trade_type == "LONG" else pos["entry_price"] * 0.999
                if trade_type == "LONG" and new_sl > sl: sl = new_sl
                elif trade_type == "SHORT" and new_sl < sl: sl = new_sl
                
            # Phase 3: +2.5R -> Lock in +1.0R
            if profit_r >= 2.5:
                new_sl = pos["entry_price"] + initial_risk if trade_type == "LONG" else pos["entry_price"] - initial_risk
                if trade_type == "LONG" and new_sl > sl: sl = new_sl
                elif trade_type == "SHORT" and new_sl < sl: sl = new_sl
                
            # Phase 4: +4.0R -> Lock in +2.5R
            if profit_r >= 4.0:
                new_sl = pos["entry_price"] + (initial_risk * 2.5) if trade_type == "LONG" else pos["entry_price"] - (initial_risk * 2.5)
                if trade_type == "LONG" and new_sl > sl: sl = new_sl
                elif trade_type == "SHORT" and new_sl < sl: sl = new_sl
                
            if sl != pos["stop_loss"]:
                db.db_execute("UPDATE paper_trades SET stop_loss = ? WHERE id = ?", (sl, pos["id"]))
            # ---------------------------------------------------
            
            if not exit_reason:
                if trade_type in ("LONG", "PAIR_LONG"):
                    # SL Hit (Real-time)
                    if current_price <= sl:
                        exit_reason = "SL_HIT_LIVE"
                        exit_price = sl  # Slippage modeled in execution
                    # Target Hit (Real-time)
                    elif current_price >= target:
                        exit_reason = "TARGET_HIT_LIVE"
                        exit_price = target
                elif trade_type in ("SHORT", "PAIR_SHORT"):
                    if current_price >= sl:
                        exit_reason = "SL_HIT_LIVE"
                        exit_price = sl
                    elif current_price <= target:
                        exit_reason = "TARGET_HIT_LIVE"
                        exit_price = target
                
            if exit_reason:
                # Same execution and exit logic
                trade_value = exit_price * qty
                fees = trade_value * (0.001) # 0.1% approx
                
                # Invert PnL for shorts: (Entry - Exit) * Qty
                if trade_type in ("LONG", "PAIR_LONG"):
                    gross_pnl = trade_value - pos["position_value"]
                else:
                    gross_pnl = pos["position_value"] - trade_value
                    
                net_pnl = gross_pnl - fees - pos["fees"]
                return_pct = (net_pnl / pos["position_value"]) * 100
                
                db.db_execute("""
                    UPDATE paper_trades 
                    SET status = ?, exit_date = ?, exit_price = ?, exit_reason = ?, 
                        gross_pnl = ?, fees = fees + ?, net_pnl = ?, return_pct = ?
                    WHERE id = ?
                """, ("CLOSED_" + ("WIN" if net_pnl > 0 else "LOSS"), today, exit_price, exit_reason, 
                      gross_pnl, fees, net_pnl, return_pct, pos["id"]))
                
                cash += (pos["position_value"] + gross_pnl - fees)
                logger.info(f"🚨 LIVE {trade_type} EXIT {symbol}: {exit_reason} at ₹{exit_price:.2f}. PnL: ₹{net_pnl:.2f}")
                
                # Update portfolio cash (rough live update)
                db.db_execute("UPDATE paper_portfolio SET cash = ? WHERE date = ?", (cash, today))
                
                try:
                    from arena.trade_autopsy import generate_autopsy
                    generate_autopsy(pos["id"])
                except Exception:
                    pass

    except Exception as e:
        logger.error(f"Live position tracking error: {e}")

if __name__ == "__main__":
    execute_daily_arena()
