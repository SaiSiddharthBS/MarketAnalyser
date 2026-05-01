# Agent Alpha - Technical Handover Document

## Project Overview
Agent Alpha is a high-performance market analysis and paper trading platform built for stability in cloud environments. It integrates live market data, sentiment analysis, and automated Telegram alerts.

## Tech Stack
- **Backend**: FastAPI (Python 3.12.3)
- **Web Server**: Gunicorn + UvicornWorker (Timeout: 120s)
- **Database**: 
  - **Local**: SQLite (WAL mode enabled)
  - **Cloud**: PostgreSQL (Neon.tech)
  - **Abstraction**: `backend/database.py` provides a universal `db_execute` wrapper.
- **Frontend**: Vanilla HTML5, CSS3, ES6 Javascript.
- **Deployment**: Render.com (Auto-deploy from GitHub).
- **CI/CD**: GitHub Actions for daily automated briefings.

## Critical Stability Features (Don't Remove!)
1. **Cloud IP Bypass**: `backend/data/stock_fetcher.py` uses a custom `requests.Session` with browser headers to prevent Yahoo Finance from blocking Render IPs.
2. **Parallel Fetching**: `backend/main.py` uses `asyncio.gather` and `run_in_threadpool` to fetch market data in parallel, preventing 502 Bad Gateway timeouts.
3. **Neon Connection Pool**: PostgreSQL pool is limited to **5 connections** to prevent "Connection Refused" errors on Neon.tech Free Tier.
4. **Holiday Detection**: `backend/bot/daily_job.py` detects zero-change days (holidays) and sends an appropriate greeting instead of empty data.
5. **Keep-Alive**: `main.py` contains a self-ping background task to prevent Render Free Tier from sleeping.

## Environment Secrets
Ensure these are set in both Render Dashboard and GitHub Secrets:
- `DATABASE_URL`: PostgreSQL connection string.
- `TELEGRAM_BOT_TOKEN`: Telegram bot credentials.
- `TELEGRAM_CHAT_ID`: User's telegram ID.
- `PYTHON_VERSION`: 3.12.3

## Code Architecture
- `backend/main.py`: Entry point, API routes, and keep-alive logic.
- `backend/database.py`: Core DB operations and universal SQL translator.
- `backend/data/`:
    - `stock_fetcher.py`: yfinance integration with anti-blocking.
    - `news_fetcher.py`: News scraping and VADER sentiment analysis.
- `backend/bot/daily_job.py`: Logic for the Telegram briefing.
- `frontend/`: 
    - `js/api.js`: Centralized API client.
    - `js/app.js`: UI logic and state management.

## Future Roadmap (Phase 2)
- **ML Integration**: `backend/analysis/ml_engine.py` is ready for advanced prediction models.
- **Screener Expansion**: Add more technical indicators to the automated scanner.
- **Portfolio Analytics**: Add XIRR and CAGR calculations to the Paper Trading module.

---
**Handover Note for the Next AI**: 
This system is highly optimized for cloud hosting. Do not change the `session` headers in `stock_fetcher.py` or the `pool` size in `database.py` without testing on Render first.
