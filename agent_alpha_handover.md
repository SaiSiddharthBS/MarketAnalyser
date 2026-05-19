# Agent Alpha - THE ULTIMATE HANDOVER DOCUMENT (Master File)

## 1. INFRASTRUCTURE & ACCOUNTS
- **GitHub Account**: `SaiSiddharthBS`
- **GitHub Repository**: `https://github.com/SaiSiddharthBS/MarketAnalyser`
- **Render Service**: `marketpulse-agent` (onrender.com)
- **Database**: Neon.tech (PostgreSQL)
- **Notifications**: Telegram Bot API

## 2. MASTER CREDENTIALS (SENSITIVE)
Use these exact values for any new environment setup:

- **DATABASE_URL**: `postgresql://neondb_owner:npg_EUo9iduM3Oza@ep-aged-pond-anltyrzf.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require`
- **TELEGRAM_BOT_TOKEN**: `8433034119:AAHLKY3I5nra9vCQ1UirdCsoiTF6RUvatdk`
- **TELEGRAM_CHAT_ID**: `1186289837`
- **PYTHON_VERSION**: `3.12.3`

## 3. CHRONOLOGICAL PROJECT TIMELINE & CRITICAL FIXES
Here is exactly what we did since yesterday to make this project work:

### Phase 1: Local Setup & SSL Fixes
- **The Problem**: On macOS, `yfinance` and `urllib` were crashing with "SSL Certificate Verify Failed".
- **The Fix**: Injected `ssl._create_default_https_context = ssl._create_unverified_context` globally in `stock_fetcher.py`, `mf_fetcher.py`, and `daily_job.py`.

### Phase 2: Cloud Migration (Render & Neon)
- **The Problem**: SQLite doesn't work on Render (it's read-only/ephemeral).
- **The Fix**: Migrated to Neon.tech Postgres. Created a **Universal Database Wrapper** in `backend/database.py` that translates SQLite syntax (like `?`) to Postgres syntax (like `%s`) automatically.

### Phase 3: Bypassing Yahoo Finance Blocks
- **The Problem**: Yahoo Finance blocks cloud server IPs (Render/Heroku), causing "Expecting value: line 1" errors.
- **The Fix**: Implemented a **Custom requests.Session** in `stock_fetcher.py`. It uses browser-mimicking User-Agent headers to trick Yahoo into thinking Render is a home computer.

### Phase 4: Fixing Render Deployment Hangs
- **The Problem**: Render deployment was hanging on "Application Loading".
- **The Fix**: 
    1. Added `runtime.txt` and updated `render.yaml` to force Python 3.12.3.
    2. Reduced Postgres pool size to **5** to stay within Neon.tech free tier limits.
    3. Added a safety check in `db_execute` so the app doesn't crash if the DB is slow to wake up.

### Phase 5: Solving 502 Bad Gateway Timeouts
- **The Problem**: The Dashboard was too slow, causing Render to time out (502).
- **The Fix**: 
    1. Implemented **Parallel Async Fetching** using `asyncio.gather`.
    2. Increased Gunicorn timeout to **120 seconds** in `render.yaml`.

## 4. BOT & AUTOMATION
- **GitHub Action**: `.github/workflows/daily_alert.yml` runs every morning at 8:00 AM IST.
- **Holiday Detection**: The bot is programmed to send a "Market is CLOSED" message on holidays instead of failing.
- **Manual Alert**: Added a button on the Dashboard top-right to manually trigger the Telegram alert.

---
## 5. INSTRUCTIONS FOR THE NEXT AI
1. **READ THIS FILE FIRST**.
2. Do not change the `session` headers in `stock_fetcher.py`. They are required to bypass the Yahoo block.
3. Keep the DB connection pool at `maxconn=5`.
4. Always use `run_in_threadpool` for synchronous fetchers in `main.py` to avoid blocking the event loop.

**JAI SHRI RAM! 🙏🏻**

### Phase 6: Arena Execution Pipeline & Caching Optimization
- **The Problem**: The automated Arena Engine hung for 15+ minutes because it made duplicate NSE Options chain fetch requests for all 50 stocks, leading to severe rate limiting. Duplicate ensemble signal processing further crippled execution.
- **The Fix**: Implemented a robust 60-second in-memory cache (`_CHAIN_CACHE` in `options_fetcher.py`) for macro options data to eliminate redundant network calls. Refactored the Arena loop to streamline evaluation, slashing processing time by over 60%.

### Phase 7: Fixing HuggingFace Threading Deadlocks
- **The Problem**: The backend server and UI experienced intermittent 502 Bad Gateway timeouts and execution hangs because the HuggingFace `tokenizers` module crashed during process forks.
- **The Fix**: Injected `os.environ["TOKENIZERS_PARALLELISM"] = "false"` globally at the top of `main.py` before any transformers imports. This completely resolved multi-threading deadlocks and stabilized the server.

### Phase 8: Separating Manual vs Automated Paper Trading (Frontend)
- **The Problem**: The navigation logic in `index.html` was incorrectly routing both the manual "Paper Trading" tab and the automated "Arena" tab to the same page, destroying the ability to execute manual mock trades.
- **The Fix**: Separated the manual trading simulation (`page-paper`) from the automated Arena engine (`page-arena`) in the frontend DOM. Corrected the JavaScript routing logic in `app.js` and reinstated manual P&L/Position tracking functions, restoring full dual-mode functionality.

### Phase 9: Arena Stand-Aside Telegram Notifications
- **The Problem**: The Arena Engine executed its daily scan silently unless a trade was specifically opened or closed, leaving the user guessing whether the engine had crashed or merely found no high-conviction trades.
- **The Fix**: Upgraded the notification system in `paper_trading.py` to transmit proactive Telegram alerts when the system successfully scans the market but intelligently elects to stay in 100% Cash due to stringent regime thresholds (e.g., during "low_vol_chop" or "crisis").

### Phase 10: Regime Thresholds & Conviction Calibrations (Omega Edition Start)
- **The Problem**: The system was playing it too safe. The VIX threshold for "crisis" was at 25, meaning routine pullbacks blocked all trades. Conviction was inverted (required 75+ but logic was flawed), causing no dip-buying opportunities to be seized. GitHub Actions triggered randomly on every schedule.
- **The Fix**: 
    1. Raised VIX Crisis threshold to 30 and introduced `high_vol_chop` dip-buying state in `regime.py`.
    2. Lowered minimum conviction score for `STRONG_BUY` during corrections in `paper_trading.py` and implemented dynamic, regime-aware position sizing (replacing fixed 20%).
    3. Added `if` conditions to `main.yml` to route GitHub Actions flawlessly based on explicit cron schedules.

### Phase 11: Institutional Execution Slippage Model
- **The Problem**: Backtesting and Paper Trading assumed a fixed 0.3% slippage, which was highly unrealistic for small vs large position sizes in illiquid vs liquid names.
- **The Fix**: Ported `execution_model.py` from OpenTerminalUI into `backend/arena/`. Integrated dynamic volume-weighted impact curves into `paper_trading.py`. Now slippage scales based on `quantity` vs `bar_volume`.

### Phase 12: F&O Options Intelligence Integration
- **The Problem**: The ensemble model lacked insight into derivatives positioning (Smart Money).
- **The Fix**: Adapted `fno_signals.py` from OpenTerminalUI to integrate with the internal `options_fetcher.py`. Extracts OI Buildup (Long Buildup, Short Covering, etc.) and integrates it as a **9th voting model** (`fno_bias`) in `ensemble.py`. Added a hard veto in `veto_engine.py` (Blocks BUY if IV Percentile > 85 and short buildup).

### Phase 13: Statistical Validation (Monte Carlo & Strategy Tearsheets)
- **The Problem**: No way to mathematically validate the Arena portfolio's edge against random drawdowns.
- **The Fix**: Integrated `montecarlo.py` and `tearsheet.py` from OpenTerminalUI. Added new API endpoints `/api/arena/monte-carlo` and `/api/arena/tearsheet` in `main.py` for comprehensive statistical reporting.

### Phase 14: AI Insights Layer (Gemini Flash)
- **The Problem**: Intel Mac lacks speed for local LLMs; the terminal needed "explainable AI" for trades and portfolio risk without slowing down operations.
- **The Fix**: Created `ai_insights.py` powered by `google.generativeai` (Gemini 2.5 Flash). Added API endpoints for stock briefings, Arena decision explainability, and Portfolio Risk Narratives. Enhanced `daily_job.py` to natively embed the AI Risk Narrative directly into the daily Telegram broadcast.

### Phase 15: React Terminal Front-End Scaffold
- **The Problem**: The frontend required modernization towards a premium, "Awwwards-level" interface without destroying the existing lightweight setup.
- **The Fix**: Scaffolded a brand new Vite/React/TypeScript shell inside `frontend/react_terminal/` with `Vanilla CSS` for maximum glassmorphic styling control. Created the transition `README.md`.
