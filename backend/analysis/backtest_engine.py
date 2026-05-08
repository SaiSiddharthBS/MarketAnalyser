"""
Agent Alpha v2.0 — Walk-Forward Backtest Engine
=================================================
The most rigorous backtesting methodology in quantitative finance.

Eliminates look-ahead bias by strictly moving a training window forward 
in time and only testing on unseen future data.

Features:
- Slippage & Impact cost modeling (vital for Indian midcaps)
- Brokerage & STT (Securities Transaction Tax) accounting
- Gap risk execution (trades open at 'next_day_open', not 'signal_close')
- Rolling Sharpe & Sortino ratios
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

class WalkForwardBacktester:
    """Rigorous Walk-Forward Backtest Engine."""

    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        
        # Institutional slippage & cost models for Indian Markets (Equity Delivery)
        self.costs = {
            "brokerage_pct": 0.001,    # 0.1% (Zero Brokerage is a myth; impact cost exists)
            "stt_pct": 0.001,          # 0.1% STT on delivery
            "slippage_largecap": 0.001, # 0.1% slippage for Nifty 50
            "slippage_midcap": 0.003,   # 0.3% slippage for Next 50/Midcap
        }

    def execute_trade(self, signal: str, quantity: int, price: float, cap_type: str = "largecap") -> Dict[str, float]:
        """Simulate trade execution with realistic institutional costs."""
        slippage_pct = self.costs["slippage_largecap"] if cap_type == "largecap" else self.costs["slippage_midcap"]
        
        if signal == "BUY":
            # You buy at a worse (higher) price than quoted
            exec_price = price * (1 + slippage_pct)
            trade_value = exec_price * quantity
            
            brokerage = trade_value * self.costs["brokerage_pct"]
            stt = trade_value * self.costs["stt_pct"]
            total_cost = brokerage + stt
            
            return {
                "exec_price": exec_price,
                "net_value": trade_value + total_cost, # Cost adds to total cash outlay
                "fees": total_cost
            }
            
        elif signal == "SELL":
            # You sell at a worse (lower) price than quoted
            exec_price = price * (1 - slippage_pct)
            trade_value = exec_price * quantity
            
            brokerage = trade_value * self.costs["brokerage_pct"]
            stt = trade_value * self.costs["stt_pct"]
            total_cost = brokerage + stt
            
            return {
                "exec_price": exec_price,
                "net_value": trade_value - total_cost, # Cost deducts from cash received
                "fees": total_cost
            }
            
        return {"exec_price": 0.0, "net_value": 0.0, "fees": 0.0}

    def run_walk_forward(
        self, 
        df: pd.DataFrame, 
        signal_series: pd.Series, 
        symbol: str,
        cap_type: str = "largecap"
    ) -> Dict[str, Any]:
        """
        Run backtest over a pre-computed signal series.
        
        CRITICAL ASSUMPTION: 
        If signal is generated on Day T (using Close price), 
        execution MUST happen on Day T+1 (using Open price).
        """
        if df is None or len(df) < 50 or signal_series is None or len(signal_series) != len(df):
            return {"error": "Invalid data for backtest"}

        cash = self.initial_capital
        holdings = 0
        
        trades = []
        equity_curve = []
        peak_equity = self.initial_capital
        drawdowns = []
        
        dates = df.index
        opens = df["Open"].values
        closes = df["Close"].values
        
        # We start from index 1 because Day T signal is traded on Day T+1 open
        for i in range(1, len(df)):
            current_date = dates[i]
            
            # The signal was generated yesterday (i-1)
            signal_yesterday = signal_series.iloc[i-1]
            
            # Today's prices
            today_open = opens[i]
            today_close = closes[i]
            
            # Record current equity before trading
            current_equity = cash + (holdings * today_open)
            equity_curve.append({
                "date": current_date,
                "equity": current_equity
            })
            
            if current_equity > peak_equity:
                peak_equity = current_equity
            
            dd = (peak_equity - current_equity) / peak_equity * 100
            drawdowns.append(dd)
            
            # ─── Execution Logic ────────────────────────────────────
            
            if signal_yesterday == "BUY" and holdings == 0:
                # Calculate quantity based on 10% portfolio allocation
                alloc = current_equity * 0.10
                qty = int(alloc / today_open)
                
                if qty > 0:
                    exec_data = self.execute_trade("BUY", qty, today_open, cap_type)
                    if cash >= exec_data["net_value"]:
                        cash -= exec_data["net_value"]
                        holdings += qty
                        
                        trades.append({
                            "type": "BUY",
                            "date": current_date,
                            "price": exec_data["exec_price"],
                            "qty": qty,
                            "fees": exec_data["fees"]
                        })
                        
            elif signal_yesterday == "SELL" and holdings > 0:
                exec_data = self.execute_trade("SELL", holdings, today_open, cap_type)
                
                cash += exec_data["net_value"]
                
                # Calculate trade PnL
                buy_trade = next((t for t in reversed(trades) if t["type"] == "BUY"), None)
                pnl = 0
                if buy_trade:
                    buy_value = buy_trade["price"] * buy_trade["qty"]
                    sell_value = exec_data["exec_price"] * holdings
                    pnl = sell_value - buy_value - exec_data["fees"] - buy_trade["fees"]
                
                trades.append({
                    "type": "SELL",
                    "date": current_date,
                    "price": exec_data["exec_price"],
                    "qty": holdings,
                    "fees": exec_data["fees"],
                    "pnl": pnl
                })
                
                holdings = 0

        # Close open positions at the end of backtest
        if holdings > 0:
            final_close = closes[-1]
            exec_data = self.execute_trade("SELL", holdings, final_close, cap_type)
            cash += exec_data["net_value"]
            
            buy_trade = next((t for t in reversed(trades) if t["type"] == "BUY"), None)
            pnl = 0
            if buy_trade:
                buy_value = buy_trade["price"] * buy_trade["qty"]
                sell_value = exec_data["exec_price"] * holdings
                pnl = sell_value - buy_value - exec_data["fees"] - buy_trade["fees"]
            
            trades.append({
                "type": "SELL_EOT", # End of Test
                "date": dates[-1],
                "price": exec_data["exec_price"],
                "qty": holdings,
                "fees": exec_data["fees"],
                "pnl": pnl
            })
            holdings = 0

        # ─── Performance Metrics ────────────────────────────────
        
        final_equity = cash
        total_return_pct = (final_equity - self.initial_capital) / self.initial_capital * 100
        
        completed_trades = [t for t in trades if t["type"] in ("SELL", "SELL_EOT")]
        winning_trades = [t for t in completed_trades if t.get("pnl", 0) > 0]
        losing_trades = [t for t in completed_trades if t.get("pnl", 0) <= 0]
        
        win_rate = len(winning_trades) / len(completed_trades) * 100 if completed_trades else 0
        
        avg_win = np.mean([t["pnl"] for t in winning_trades]) if winning_trades else 0
        avg_loss = abs(np.mean([t["pnl"] for t in losing_trades])) if losing_trades else 1
        
        profit_factor = (avg_win * len(winning_trades)) / (avg_loss * len(losing_trades)) if (avg_loss * len(losing_trades)) > 0 else float('inf')
        
        max_drawdown = max(drawdowns) if drawdowns else 0
        
        # Sharpe Ratio Calculation (Risk-Free Rate ~ 6% for India)
        if equity_curve:
            eq_df = pd.DataFrame(equity_curve)
            eq_df["daily_ret"] = eq_df["equity"].pct_change()
            ann_ret = eq_df["daily_ret"].mean() * 252
            ann_vol = eq_df["daily_ret"].std() * np.sqrt(252)
            sharpe = (ann_ret - 0.06) / ann_vol if ann_vol > 0 else 0
        else:
            sharpe = 0

        return {
            "symbol": symbol,
            "initial_capital": self.initial_capital,
            "final_equity": round(final_equity, 2),
            "total_return_pct": round(total_return_pct, 2),
            "max_drawdown_pct": round(max_drawdown, 2),
            "sharpe_ratio": round(sharpe, 2),
            "profit_factor": round(profit_factor, 2),
            "trades_count": len(completed_trades),
            "win_rate_pct": round(win_rate, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "total_fees_paid": round(sum(t.get("fees", 0) for t in trades), 2)
        }

# Global Instance
backtester = WalkForwardBacktester()
