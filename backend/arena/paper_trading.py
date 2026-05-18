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

IST = pytz.timezone("Asia/Kolkata")

INITIAL_CAPITAL = 1_000_000  # ₹10 Lakh
MAX_POSITIONS = 5
SLIPPAGE_PCT = 0.003         # 0.3%
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
        
        # SL Hit
        if today_low <= sl:
            exit_reason = "SL_HIT"
            exit_price = sl * (1 - SLIPPAGE_PCT)
        # Target Hit
        elif today_high >= target:
            exit_reason = "TARGET_HIT"
            exit_price = target * (1 - SLIPPAGE_PCT)
        # Timeout
        elif days_held >= MAX_HOLD_DAYS:
            exit_reason = "TIMEOUT_15D"
            exit_price = today_open * (1 - SLIPPAGE_PCT)
        
        if exit_reason:
            trade_value = exit_price * qty
            fees = trade_value * (BROKERAGE_PCT + STT_PCT)
            net_pnl = trade_value - pos["position_value"] - fees - pos["fees"]
            gross_pnl = trade_value - pos["position_value"]
            return_pct = (net_pnl / pos["position_value"]) * 100
            
            # Close trade
            db.db_execute("""
                UPDATE paper_trades 
                SET status = ?, exit_date = ?, exit_price = ?, exit_reason = ?, 
                    gross_pnl = ?, fees = fees + ?, net_pnl = ?, return_pct = ?
                WHERE id = ?
            """, ("CLOSED_" + ("WIN" if net_pnl > 0 else "LOSS"), today, exit_price, exit_reason, 
                  gross_pnl, fees, net_pnl, return_pct, pos["id"]))
            
            cash += trade_value - fees
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
    if num_open < MAX_POSITIONS:
        logger.info(f"Capacity available: {MAX_POSITIONS - num_open} slots. Scanning for trades...")
        
        regime_data = get_current_market_regime()
        regime = regime_data.get("regime", "unknown")
        
        if regime == "crisis":
            logger.info("Regime is CRISIS. Not opening new positions.")
        else:
            scored_stocks = []
            for symbol in NIFTY_50_SYMBOLS:
                ticker = f"{symbol}.NS"
                df = download_ohlcv(ticker, period="6mo", interval="1d")
                if df is None or len(df) < 50: continue
                
                tech_analysis = get_technical_analysis(symbol, df)
                if not tech_analysis: continue
                
                ensemble = get_ensemble_analysis(symbol, df, regime)
                confidence = ensemble.get("confidence", 0)
                signal = ensemble.get("signal", "NEUTRAL")
                
                # Veto check
                veto = veto_engine.check_all_vetoes(symbol, {}, {"regime_state": regime, "vix": regime_data.get("vix_level", 15)}, {})
                if veto.get("vetoed") or signal != "BUY":
                    continue
                    
                conviction = "HIGH" if confidence >= 75 else ("ULTRA" if confidence >= 85 else "MODERATE")
                if conviction not in ["HIGH", "ULTRA"]:
                    continue
                    
                scored_stocks.append({
                    "symbol": symbol,
                    "confidence": confidence,
                    "conviction": conviction,
                    "ensemble": ensemble,
                    "tech": tech_analysis
                })
                
            # Sort by confidence
            scored_stocks.sort(key=lambda x: x["confidence"], reverse=True)
            
            slots_available = MAX_POSITIONS - num_open
            for candidate in scored_stocks[:slots_available]:
                symbol = candidate["symbol"]
                tech = candidate["tech"]
                ensemble = candidate["ensemble"]
                
                # Entry price is today's open + slippage
                df = download_ohlcv(f"{symbol}.NS", period="5d", interval="1d")
                if df is None or df.empty: continue
                today_open = float(df.iloc[-1]["Open"])
                
                entry_price = today_open * (1 + SLIPPAGE_PCT)
                
                alloc = min(cash, INITIAL_CAPITAL * 0.20)
                qty = int(alloc / entry_price)
                if qty == 0: continue
                
                pos_value = qty * entry_price
                fees = pos_value * (BROKERAGE_PCT + STT_PCT)
                
                if cash < (pos_value + fees):
                    continue
                
                sl = tech.get("atr_sl_long", entry_price * 0.95)
                target = entry_price + 2 * (entry_price - sl) # 2:1 RR
                
                # Store
                db.db_execute("""
                    INSERT INTO paper_trades (
                        symbol, trade_type, signal_date, entry_date, entry_price, quantity,
                        position_value, stop_loss, target_price, risk_reward_ratio, fees,
                        regime_at_entry, ensemble_score, conviction, model_votes_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    symbol, "BUY", get_current_date_ist(), today, entry_price, qty,
                    pos_value, sl, target, 2.0, fees, regime, candidate["confidence"],
                    candidate["conviction"], json.dumps(ensemble.get("votes", {}))
                ))
                
                cash -= (pos_value + fees)
                new_trades.append(symbol)
                
                msg = f"🏟️ *ARENA TRADE OPENED: {symbol}*\nQty: {qty}\nEntry: ₹{entry_price:.2f}\nTarget: ₹{target:.2f}\nSL: ₹{sl:.2f}"
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
        nifty_return = ((nifty_df["Close"].iloc[-1] / nifty_df["Close"].iloc[-2]) - 1) * 100

    # Insert or update today's snapshot
    if existing:
        db.db_execute("""
            UPDATE paper_portfolio 
            SET cash=?, holdings_value=?, total_equity=?, open_positions=?, daily_return_pct=?, cumulative_return_pct=?, drawdown_from_peak_pct=?, benchmark_nifty_return_pct=?
            WHERE date=?
        """, (cash, holdings_value, total_equity, len(open_positions), daily_return, cum_return_pct, drawdown, nifty_return, today))
    else:
        db.db_execute("""
            INSERT INTO paper_portfolio (
                date, cash, holdings_value, total_equity, open_positions, 
                daily_return_pct, cumulative_return_pct, drawdown_from_peak_pct, 
                benchmark_nifty_return_pct
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (today, cash, holdings_value, total_equity, len(open_positions), daily_return, cum_return_pct, drawdown, nifty_return))
    
    logger.info(f"Arena daily execution complete. Equity: ₹{total_equity:.2f} ({cum_return_pct:.2f}%)")

if __name__ == "__main__":
    execute_daily_arena()
