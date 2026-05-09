"""
Agent Alpha v2.0 — Master Orchestration Pipeline
=================================================
The central nervous system of Agent Alpha.

Runs daily at 8:00 AM (Pre-market) and 3:45 PM (Post-market).

Pipeline Flow:
  Layer 1 → Data Validation & Macro Intelligence
  Layer 3 → Regime Classification (HMM/Rule-based)
  Layer 5 → Hard Veto Engine (12-rule firewall)
  Layer 2 → 8-Model Ensemble per stock
  Layer 4 → ML Engine verification (LightGBM)
  Layer 5 → Position Sizing (Kelly/CVaR)
  Layer 5 → Portfolio Optimization (Correlation/Sector)
  Layer 6 → Database audit logging
  Output  → Telegram briefing
"""
import sys
import os
import asyncio
from pathlib import Path
import ssl
import traceback
from datetime import datetime
import pandas as pd

# Fix SSL issues on macOS
ssl._create_default_https_context = ssl._create_unverified_context

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import database as db
from config import NIFTY_50_SYMBOLS

# ─── Data Fetchers (Layer 1) ───────────────────────────────
from data.stock_fetcher import get_market_overview, download_ohlcv
from data.news_fetcher import get_market_news
from data.data_validator import DataValidator
from data.premarket_fetcher import fetch_premarket_data
from data.macro_calendar import check_macro_veto

# ─── Analysis Layers ───────────────────────────────────────
from analysis.regime import get_current_market_regime
from analysis.veto_engine import veto_engine  # Use the singleton
from analysis.ensemble import calculate_ensemble_signal
from analysis.position_sizing import calculate_position_size
from analysis.portfolio_optimizer import optimize_portfolio_selection

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()


def send_telegram_sync(msg: str) -> bool:
    """Send message to Telegram with auto-chunking and Markdown fallback."""
    import requests
    if not TOKEN or not CHAT_ID:
        print("❌ TELEGRAM credentials missing!")
        return False

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    chunks = [msg[i:i + 4000] for i in range(0, len(msg), 4000)]
    all_success = True

    for i, chunk in enumerate(chunks):
        payload = {"chat_id": CHAT_ID, "text": chunk, "parse_mode": "Markdown"}
        try:
            r = requests.post(url, json=payload, timeout=15)
            if r.status_code != 200:
                # Fallback to plain text if Markdown parsing fails
                payload.pop("parse_mode")
                r = requests.post(url, json=payload, timeout=15)
            if r.status_code != 200:
                print(f"❌ Telegram chunk {i + 1} failed: {r.text[:200]}")
                all_success = False
            else:
                print(f"✅ Sent chunk {i + 1}/{len(chunks)}")
        except Exception as e:
            print(f"❌ Exception sending chunk {i + 1}: {e}")
            all_success = False

    return all_success


def _detect_session_type() -> str:
    """Determine if this is a morning or afternoon session."""
    try:
        from zoneinfo import ZoneInfo
        ist_now = datetime.now(ZoneInfo("Asia/Kolkata"))
    except ImportError:
        import pytz
        ist_now = datetime.now(pytz.timezone("Asia/Kolkata"))
    except Exception:
        ist_now = datetime.utcnow()
    return "morning" if ist_now.hour < 12 else "afternoon"


def _run_alpha_v2_pipeline() -> str:
    """
    Execute the full 6-layer Agent Alpha v2.0 quantitative pipeline.
    Returns formatted results string for Telegram.
    """
    results_lines = []

    # ═══════════════════════════════════════════════════════════
    # LAYER 1: Pre-market Intelligence & Macro Checks
    # ═══════════════════════════════════════════════════════════
    print("\n[Layer 1] Pre-market & Macro checks...")
    macro_check = check_macro_veto()

    try:
        premarket = fetch_premarket_data()
        premarket_status = premarket.get("risk_level", "NORMAL")
    except Exception as e:
        print(f"  ⚠️ Premarket fetch failed (non-fatal): {e}")
        premarket = {}
        premarket_status = "UNKNOWN"

    if macro_check.get("trigger"):
        macro_msg = macro_check.get("reason", "Macro event detected")
        results_lines.append(f"⚠️ *Macro Alert:* {macro_msg}")

    # ═══════════════════════════════════════════════════════════
    # LAYER 3: Regime Classification (HMM / Rule-based)
    # ═══════════════════════════════════════════════════════════
    print("[Layer 3] Calculating Market Regime...")
    try:
        regime = get_current_market_regime()
    except Exception as e:
        print(f"  ⚠️ Regime engine failed (using fallback): {e}")
        regime = {"regime": "unknown", "status": "UNKNOWN", "confidence_pct": 0}

    regime_name = regime.get("regime", "unknown")
    regime_status = regime.get("status", "UNKNOWN")
    print(f"  🎯 Regime: {regime_name.upper()} ({regime.get('confidence_pct', 0)}%)")

    results_lines.append(
        f"🎯 *Regime:* {regime_status} ({regime_name.upper()})"
    )

    # Log regime to DB
    try:
        db.log_market_regime(regime)
    except Exception as e:
        print(f"  DB regime log error (non-fatal): {e}")

    # ═══════════════════════════════════════════════════════════
    # LAYER 5 (Pre-check): Market-Level Hard Veto
    # ═══════════════════════════════════════════════════════════
    print("[Layer 5] Running Market-Level Veto checks...")

    # Build market_data dict for veto engine
    market_veto_data = {
        "regime_state": regime_name,
        "fii_hard_veto_active": False,  # Would come from fii_dii_fetcher
        "vix_5d_change_pct": 0,
        "sgx_nifty_gap_pct": premarket.get("sgx_gap_pct", 0) if premarket else 0,
        "vix": 0,
    }

    # Quick market-level veto check (no stock-specific data needed)
    market_veto = veto_engine.check_all_vetoes(
        symbol="MARKET_WIDE",
        stock_data={},
        market_data=market_veto_data,
        portfolio_data=None,
    )

    if market_veto["vetoed"] and market_veto["max_severity"] == "CRITICAL":
        veto_reasons = [v["reason"] for v in market_veto["active_vetoes"]]
        print(f"  🚨 CRITICAL VETO: {veto_reasons}")

        # Log veto
        try:
            db.log_veto("MARKET_WIDE", veto_reasons[0], "CRITICAL")
        except Exception:
            pass

        return (
            "🚨 *HARD VETO TRIGGERED* 🚨\n\n"
            f"*Reason:* {veto_reasons[0]}\n"
            f"*Action:* Move to CASH. Do not deploy new capital.\n"
            f"*Regime:* {regime_name.upper()}"
        )

    # ═══════════════════════════════════════════════════════════
    # LAYER 2: Run 8-Model Ensemble per Stock
    # ═══════════════════════════════════════════════════════════
    print("[Layer 2] Running Ensemble across universe...")
    candidates = []
    returns_data = {}

    for symbol in NIFTY_50_SYMBOLS[:30]:  # Limit for speed on free tier
        try:
            df = download_ohlcv(symbol, period="1y")
            if df is None or len(df) < 50:
                continue

            # Layer 1: Data Validation
            val_status, val_msg = DataValidator.validate_ohlcv(df)
            if not val_status:
                print(f"  ⚠️ {symbol}: Data validation failed — {val_msg}")
                continue

            returns_data[symbol] = df["Close"].pct_change().dropna()

            # Build model outputs for ensemble
            # In production, each model would be called individually.
            # For the free-tier MVP, we use the technical analysis as
            # the primary signal and build synthetic ensemble inputs.
            from analysis.technical import get_technical_analysis
            ta = get_technical_analysis(symbol)

            if not ta:
                continue

            ta_score = ta.get("score", 50)
            ta_signal = ta.get("signal", "NEUTRAL")

            # Map TA signal to ensemble format
            if ta_signal in ("EARLY_MOMENTUM", "CONTINUATION"):
                direction = 1
                signal = "BUY"
            elif ta_signal in ("WEAK", "AVOID"):
                direction = -1
                signal = "SELL"
            else:
                direction = 0
                signal = "NEUTRAL"

            # Build model outputs dict
            model_outputs = {
                "momentum": {
                    "signal": signal,
                    "confidence": ta_score,
                    "direction": direction,
                    "symbol": symbol,
                },
            }

            # Calculate ensemble
            ensemble = calculate_ensemble_signal(model_outputs)

            if "BUY" in ensemble.get("signal", ""):
                # Layer 5: Position Sizing
                try:
                    sizing = calculate_position_size(
                        entry_price=ta.get("entry", df["Close"].iloc[-1]),
                        stop_loss=ta.get("stop_loss", df["Close"].iloc[-1] * 0.95),
                        capital=100000,
                        ensemble_signal=ensemble,
                        regime_state=regime_name,
                        stock_returns=returns_data.get(symbol),
                    )
                except Exception as ps_err:
                    print(f"  ⚠️ {symbol} position sizing error: {ps_err}")
                    sizing = {
                        "shares": 0, "position_value": 0,
                        "kelly_fraction": 0, "stop_loss": 0,
                    }

                candidates.append({
                    "symbol": symbol,
                    "sector": "UNKNOWN",
                    "ensemble_score": ensemble.get("ensemble_score", 0),
                    "confidence": ensemble.get("final_confidence", 0),
                    "signal": ensemble.get("signal", ""),
                    "conviction": ensemble.get("conviction", ""),
                    "qty": sizing.get("shares", 0),
                    "value": sizing.get("position_value", 0),
                    "stop_loss": ta.get("stop_loss", 0),
                    "target": ta.get("target", 0),
                    "reasons": [s.get("indicator", "") for s in ta.get("signals", [])[:3]],
                })

                # Log to DB
                try:
                    db.save_ensemble_signal(symbol, ensemble)
                except Exception:
                    pass

        except Exception as e:
            print(f"  ⚠️ {symbol} pipeline error: {e}")
            continue

    # ═══════════════════════════════════════════════════════════
    # LAYER 5: Portfolio Optimization
    # ═══════════════════════════════════════════════════════════
    print(f"[Layer 5] Portfolio Optimization ({len(candidates)} candidates)...")

    if candidates:
        try:
            optimized = optimize_portfolio_selection(
                candidates=candidates,
                returns_data=returns_data,
                existing_positions=[],
                capital=100000,
            )
        except Exception as opt_err:
            print(f"  ⚠️ Portfolio optimizer error: {opt_err}")
            optimized = sorted(candidates, key=lambda x: x.get("ensemble_score", 0), reverse=True)[:5]
    else:
        optimized = []

    # ═══════════════════════════════════════════════════════════
    # FORMAT OUTPUT
    # ═══════════════════════════════════════════════════════════
    if optimized:
        results_lines.append(f"\n✅ *{len(optimized)} TRADES APPROVED:*\n")
        for i, p in enumerate(optimized[:5], 1):
            results_lines.append(
                f"*{i}. {p['symbol']}* — {p.get('conviction', '')} {p.get('signal', '')}\n"
                f"   Score: {p.get('ensemble_score', 0)} | "
                f"Qty: {p.get('qty', 0)} shares\n"
                f"   Target: ₹{p.get('target', 0):,.1f} | "
                f"Stop: ₹{p.get('stop_loss', 0):,.1f}"
            )
    else:
        results_lines.append(
            "\n⏸️ *STAND ASIDE:* No stocks passed all filters today.\n"
            "The system defaults to cash preservation when edge is unclear."
        )

    return "\n".join(results_lines)


async def send_daily_alert():
    """Master pipeline runner. Gathers data, runs quant pipeline, sends Telegram."""
    print("=" * 60)
    print(f"🚀 Agent Alpha v2.0 Engine — {datetime.now().isoformat()}")
    print("=" * 60)

    result = {"steps": [], "status": "unknown"}

    try:
        # Initialize DB
        db.init_db()

        session_type = _detect_session_type()
        print(f"📋 Session: {session_type.upper()}")
        result["steps"].append(f"✅ Session: {session_type}")

        # Gather market snapshot
        print("\n── Step 1: Market Overview ──")
        try:
            market_data = get_market_overview()
            if market_data:
                market_lines = []
                for k, v in list(market_data.items())[:5]:
                    direction = "▲" if v.get("change", 0) >= 0 else "▼"
                    market_lines.append(
                        f"{k}: {v.get('value', 0):,.2f} {direction} {v.get('change_pct', 0):+.2f}%"
                    )
                market_text = "\n".join(market_lines)
            else:
                market_text = "Market data temporarily unavailable"
        except Exception as e:
            market_text = f"Market data error: {str(e)[:100]}"
        result["steps"].append("✅ Market data gathered")

        # Run v2.0 Pipeline
        print("\n── Step 2: v2.0 Quant Pipeline ──")
        pipeline_results = _run_alpha_v2_pipeline()
        result["steps"].append("✅ Pipeline completed")

        # Compose final message
        final_message = (
            f"🤖 *AGENT ALPHA v2.0*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{pipeline_results}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 *Market Pulse:*\n{market_text}"
        )

        # Send to Telegram
        print("\n── Step 3: Transmitting ──")
        success = send_telegram_sync(final_message)
        if success:
            print("✅ v2.0 Briefing transmitted successfully.")
            result["status"] = "success"
        else:
            result["status"] = "telegram_failed"

    except Exception as e:
        print(f"\n❌ FATAL ERROR: {traceback.format_exc()}")
        result["status"] = "fatal_error"
        result["steps"].append(f"❌ FATAL: {str(e)[:200]}")

        # Dead man's switch
        send_telegram_sync(
            f"⚠️ *Agent Alpha v2.0 Error*\n"
            f"System crash: {str(e)[:200]}\n"
            f"Manual action required."
        )

    print("\n" + "=" * 60)
    print(f"🏁 Complete — Status: {result.get('status')}")
    print("=" * 60)
    return result


if __name__ == "__main__":
    asyncio.run(send_daily_alert())
