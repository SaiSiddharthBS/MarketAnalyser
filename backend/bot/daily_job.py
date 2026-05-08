"""
Agent Alpha v2.0 — Master Orchestration Pipeline
=================================================
Runs daily at 8:00 AM (Pre-market) and 3:45 PM (Post-market data aggregation).

Pipeline flow:
1. Data Validation
2. Regime Classification (HMM)
3. Hard Veto Engine
4. 8-Layer Ensemble Calculation
5. ML Engine Verification
6. Position Sizing (Kelly/CVaR)
7. Portfolio Optimization
8. Telegram Briefing Generation
"""
import sys
import os
import asyncio
from pathlib import Path
import ssl
import traceback
from datetime import datetime
import pandas as pd

# Fix SSL issues
ssl._create_default_https_context = ssl._create_unverified_context

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from telegram import Bot
import database as db
from config import NIFTY_50_SYMBOLS, USER_MF_HOLDINGS, ALPHA_CONFIG

# Data Fetchers
from data.stock_fetcher import get_market_overview, download_ohlcv
from data.news_fetcher import get_market_news
from data.mf_fetcher import get_mf_nav, get_mf_portfolio_value
from data.data_validator import DataValidator
from data.premarket_fetcher import fetch_premarket_data
from data.macro_calendar import check_macro_veto
from data.alt_data_fetcher import fetch_reddit_sentiment, fetch_google_trends_spike

# Analysis Layers
from analysis.regime import get_current_market_regime
from analysis.veto_engine import run_veto_engine
from analysis.ensemble import calculate_ensemble_score
from analysis.position_sizing import calculate_optimal_position
from analysis.portfolio_optimizer import optimize_portfolio_selection
from analysis.advisor import generate_financial_advice
from analysis.transformer_engine import predict_with_transformer

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()


def send_telegram_sync(msg: str) -> bool:
    import requests
    if not TOKEN or not CHAT_ID:
        print("❌ TELEGRAM credentials missing!")
        return False
        
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    chunks = [msg[i:i+4000] for i in range(0, len(msg), 4000)]
    all_success = True

    for i, chunk in enumerate(chunks):
        payload = {"chat_id": CHAT_ID, "text": chunk, "parse_mode": "Markdown"}
        try:
            r = requests.post(url, json=payload, timeout=15)
            if r.status_code != 200:
                payload.pop("parse_mode")
                r = requests.post(url, json=payload, timeout=15)
            if r.status_code != 200:
                print(f"❌ Telegram Error: {r.text[:200]}")
                all_success = False
        except Exception as e:
            print(f"❌ Exception sending chunk {i+1}: {e}")
            all_success = False

    return all_success


def _run_alpha_v2_pipeline() -> str:
    """
    The core Agent Alpha v2.0 Pipeline.
    """
    print("\n[Layer 1] Running Pre-market, Macro & Alt-Data checks...")
    macro_check = check_macro_veto()
    premarket = fetch_premarket_data()
    reddit_sentiment = fetch_reddit_sentiment()
    print(f"🌍 Reddit Euphoria Ratio: {reddit_sentiment.get('retail_sentiment_ratio', 0.5)}")

    
    print("[Layer 3] Calculating Market Regime (HMM)...")
    regime = get_current_market_regime()
    regime_name = regime.get("regime", "unknown")
    
    print(f"🎯 Current Regime: {regime_name.upper()} ({regime.get('confidence_pct')}%)")
    
    # Log regime to DB
    try:
        db.log_market_regime(regime)
    except Exception as e:
        print(f"DB Error (Regime): {e}")

    # Fetch Nifty data for Veto Engine
    nifty_df = download_ohlcv("^NSEI", period="1y")
    nifty_close = nifty_df["Close"].iloc[-1] if nifty_df is not None else 22000

    print("[Layer 5] Running Hard Veto Engine...")
    veto_status = run_veto_engine(
        nifty_df=nifty_df,
        fii_data={"net_flow_cr": 0}, # Would use fii_dii_fetcher in full prod
        regime=regime_name,
        macro_event_trigger=macro_check.get("trigger", False)
    )
    
    if veto_status["is_vetoed"]:
        print(f"🚨 HARD VETO TRIGGERED: {veto_status['reason']}")
        return f"""
🚨 **HARD VETO TRIGGERED** 🚨
The Systemic Firewall has blocked all new trades.
**Reason:** {veto_status['reason']}
**Action:** Move to CASH. Do not deploy new capital.
**Regime:** {regime_name.upper()}
"""

    print("[Layer 2] Running 8-Model Ensemble across Nifty 50...")
    candidates = []
    returns_data = {}
    
    for symbol in NIFTY_50_SYMBOLS:
        df = download_ohlcv(symbol, period="2y")
        
        # [Layer 1] Data Validation
        val_status, val_msg = DataValidator.validate_ohlcv(df)
        if not val_status:
            continue
            
        returns_data[symbol] = df["Close"].pct_change()
        
        # Calculate ensemble
        ensemble = calculate_ensemble_score(df, symbol)
        
        # [Layer 4] PyTorch Transformer Verification
        transformer_result = predict_with_transformer(df)
        
        # [Layer 1 Alt-Data] Google Trends Verification
        trends = fetch_google_trends_spike(symbol)
        
        # Check if Retail is Crowding this stock (Contrarian Signal)
        retail_crowding = trends.get("spike_detected", False) and reddit_sentiment.get('retail_sentiment_ratio', 0.5) > 0.7
        
        # Only buy if Ensemble is positive, Transformer agrees, and retail is NOT crowding
        if ensemble["signal"] == "BUY" and transformer_result.get("signal") != "SELL" and not retail_crowding:
            
            # [Layer 5] Position Sizing (Kelly/CVaR)
            win_rate = 0.60 # Placeholder, would come from DB model_performance
            win_loss_ratio = 1.5 
            
            sizing = calculate_optimal_position(
                df, win_rate, win_loss_ratio, portfolio_capital=100000, 
                regime=regime_name, volatility_scale=1.0
            )
            
            candidate = {
                "symbol": symbol,
                "sector": "UNKNOWN", # Would use mapping
                "ensemble_score": ensemble["ensemble_score"],
                "confidence": ensemble["final_confidence"],
                "transformer_score": transformer_result.get("prediction_score", 0),
                "kelly_multiplier": sizing["kelly_multiplier"],
                "qty": sizing["suggested_shares"],
                "value": sizing["position_value"],
                "stop_loss": sizing["stop_loss"],
                "target": sizing["target_price"],
                "reasons": ensemble["top_reasons"] + [f"Deep Learning: {transformer_result.get('signal')}"]
            }
            candidates.append(candidate)
            
            # Log signal
            try:
                db.save_ensemble_signal(symbol, ensemble)
            except Exception:
                pass

    print("[Layer 5] Running Portfolio Optimizer (Correlation Checks)...")
    # In a real run, existing_positions would be fetched from db.get_holdings()
    optimized_portfolio = optimize_portfolio_selection(
        candidates, returns_data, existing_positions=[], capital=100000
    )
    
    # Format Results
    lines = [
        f"🎯 **System Regime:** {regime.get('status')} ({regime_name.upper()})",
        f"🧩 **Crisis Prob:** {regime.get('crisis_probability_tomorrow_pct')}%\n"
    ]
    
    if optimized_portfolio:
        lines.append(f"✅ **{len(optimized_portfolio)} TRADES APPROVED (Post-Optimization):**\n")
        for p in optimized_portfolio[:5]:
            lines.append(
                f"**{p['symbol']}** — Score: {p['ensemble_score']}/100\n"
                f"• Size: {p['qty']} shares (₹{p['value']:,.0f})\n"
                f"• Multiplier: {p['kelly_multiplier']}x Kelly\n"
                f"• Target: ₹{p['target']:.1f} | Stop: ₹{p['stop_loss']:.1f}\n"
                f"• Drivers: {', '.join(p['reasons'][:2])}\n"
            )
    else:
        lines.append("⏸️ **STAND ASIDE:** No stocks passed the Ensemble + Correlation filters today.")
        
    return "\n".join(lines)


async def send_daily_alert():
    """Master Pipeline Runner."""
    print("=" * 60)
    print(f"🚀 Agent Alpha v2.0 Engine Starting — {datetime.now().isoformat()}")
    print("=" * 60)

    try:
        # Initialize DB
        db.init_db()
        
        print("\n── Step 1: Gathering Market Data ──")
        market_data = get_market_overview()
        market_text = "\n".join([f"{k}: {v['value']} ({v['change_pct']}%)" for k, v in market_data.items()][:5]) if market_data else "N/A"
        
        print("\n── Step 2: Running v2.0 Quant Pipeline ──")
        pipeline_results = _run_alpha_v2_pipeline()
        
        print("\n── Step 3: Generating LLM Synthesis ──")
        final_message = (
            "🤖 *AGENT ALPHA v2.0 — INSTITUTIONAL BRIEFING*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{pipeline_results}\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"*Market Pulse:* {market_text}"
        )
        
        print("\n── Step 4: Transmitting ──")
        success = send_telegram_sync(final_message)
        if success:
            print("✅ v2.0 Briefing Transmitted.")
            
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {traceback.format_exc()}")
        send_telegram_sync(f"⚠️ *Agent Alpha v2.0 Error* \nSystem crash: {str(e)[:200]}")

if __name__ == "__main__":
    asyncio.run(send_daily_alert())
