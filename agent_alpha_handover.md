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
