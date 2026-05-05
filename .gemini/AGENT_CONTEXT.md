# Agent Alpha — MarketPulse: Project Context & History

> **IMPORTANT FOR ANY AI ASSISTANT**: This file is the single source of truth for this project.
> Read this FIRST before doing anything. It contains the full history, architecture, and user preferences.
> This file exists so that Sai can switch between different accounts/sessions without losing context.

---

## Project Owner
- **Name**: Sai (Sai Siddharth BS)
- **GitHub**: SaiSiddharthBS/MarketAnalyser
- **Communication Style**: Treats the AI as an elder brother. Expects warmth, honesty, and no BS.
- **KEY REQUEST**: Be extremely efficient with credits. Don't waste tokens on unnecessary exploration or re-reading files that haven't changed. Be direct and execute.

## What is This Project?
**MarketPulse Agent Alpha** — A personal AI-powered financial advisor and market dashboard that:
1. **Web Dashboard** (Frontend): Premium dark-themed glassmorphism UI at the deployed Render URL
2. **Backend API** (FastAPI): Serves market data, portfolio, screener, signals, paper trading
3. **Telegram Bot**: Sends daily AI briefings at **8:00 AM** and **2:45 PM IST** via Render cron jobs
4. **AI Advisor**: Uses **Gemini 2.5 Flash** to generate personalized BUY/SELL/HOLD recommendations
5. **ML Engine**: RandomForest models for predicting 10-day price movements on Nifty 50 stocks

## Deployment
- **Platform**: Render.com (free tier web service + 2 cron jobs)
- **Database**: Neon.tech PostgreSQL (free tier, env var `DATABASE_URL`)
- **Config**: `render.yaml` defines the web service + 2 cron jobs (morning-briefing, afternoon-briefing)
- **Keep-Alive**: Self-ping every 10 minutes to prevent Render free-tier sleep

## Sai's Investor Profile
- **Experience**: Complete beginner — just started investing (as of May 2026)
- **Risk Tolerance**: Conservative-Moderate (small calculated risks OK, no huge bets)
- **Monthly Budget**: ~₹50,000 flexible (can go up to ₹1L+ for confirmed dip opportunities)
- **Platforms**: Groww, Zerodha Kite
- **EXCLUDED**: No Crypto, No Foreign/US Stocks
- **INCLUDED**: Indian Stocks, MFs, Gold (SGBs/ETFs), FDs, Bonds, PPF, NPS, REITs, Smallcase, ETFs

### Current Holdings (as of May 2026)
| Fund | Scheme Code | Invested | Units |
|------|-------------|----------|-------|
| ICICI Prudential Nifty 50 Index Fund | 120620 | ₹40,998 | 161.7885 |
| SBI Gold Fund | 119788 | ₹35,998 | 718.7280 |
| ICICI Prudential Multi Asset Fund | 120334 | ₹27,999 | 31.1605 |

**Total Invested**: ~₹1,04,995

## Architecture Overview

```
Market Analyser/
├── backend/
│   ├── main.py              # FastAPI app (all API routes)
│   ├── config.py             # Constants, stock universe, MF holdings, risk params
│   ├── database.py           # SQLite (local) / PostgreSQL (cloud) dual-mode DB
│   ├── seed_cloud.py         # One-time script to seed cloud DB with MF holdings
│   ├── analysis/
│   │   ├── advisor.py        # Gemini AI prompt engine (v2.0 - "Big Brother" persona)
│   │   ├── technical.py      # RSI, MACD, EMA, BB, ADX analysis + stock screener
│   │   └── ml_engine.py      # RandomForest model for 10-day price prediction
│   ├── bot/
│   │   ├── telegram_bot.py   # Telegram command handlers (/start, /market, /analyze, etc.)
│   │   └── daily_job.py      # Cron job engine — gathers ALL data, calls advisor, sends Telegram
│   └── data/
│       ├── stock_fetcher.py  # yfinance + Yahoo API fallback for OHLCV data
│       ├── news_fetcher.py   # Google News RSS + Yahoo News + VADER sentiment
│       └── mf_fetcher.py     # MFAPI.in for mutual fund NAV data
├── frontend/
│   ├── index.html            # Single-page app with 7 sections
│   ├── manifest.json         # PWA manifest for "Add to Home Screen"
│   ├── sw.js                 # Service worker for offline caching
│   ├── css/styles.css        # Premium dark glassmorphism theme
│   ├── js/
│   │   ├── app.js            # Main application logic, page routing, rendering
│   │   ├── api.js            # API client (fetch wrapper)
│   │   └── charts.js         # TradingView Lightweight Charts integration
│   └── images/               # PWA icons (192, 512, apple-touch, favicons)
├── render.yaml               # Render deployment config (web + 2 cron jobs)
├── requirements.txt          # Python dependencies
└── .env                      # Local env vars (not committed)
```

## Key Technical Decisions
1. **Dual DB**: SQLite for local dev, PostgreSQL (Neon.tech) for cloud. Abstracted in `database.py`
2. **Yahoo Finance Fallback**: `stock_fetcher.py` has a direct Yahoo v8 API fallback for cloud environments where yfinance is IP-blocked
3. **Gemini Model**: Using `gemini-2.5-flash` (high quota, good quality) — NOT gemini-pro
4. **Telegram Delivery**: Uses raw HTTP `requests.post()` to send messages (not the telegram library's async send), with Markdown fallback to plain text if Markdown parsing fails
5. **Screener**: Runs on all 50 Nifty stocks, scores 0-100 based on RSI/MACD/EMA/BB/ADX signals
6. **PWA**: Full Progressive Web App with service worker, manifest, and iOS meta tags for home screen app experience

## Telegram Briefing Schedule (via Render Cron Jobs)
| Time (IST) | Cron (UTC) | Type | Description |
|------------|------------|------|-------------|
| 8:00 AM | `30 2 * * *` | Morning | Full strategic briefing with screener, BUY/SELL calls, portfolio review |
| 2:45 PM | `15 9 * * *` | Afternoon | Quick tactical update, what happened, closing strategy |

## Change Log
- **2026-04-30**: Initial build — dashboard, portfolio, screener, paper trading
- **2026-05-01**: Added Telegram bot, Gemini AI advisor, deployed to Render
- **2026-05-04**: Fixed yfinance cloud issues (Yahoo API fallback), switched to gemini-2.5-flash, added keep-alive ping, added PWA support, upgraded mobile CSS
- **2026-05-05**: **Major upgrade** — Revamped AI advisor to "Big Brother" persona with specific BUY/SELL/HOLD calls across all Indian asset classes. Revamped daily_job.py to feed rich data (live MF NAVs, screener results, dip candidates). Added morning vs afternoon briefing differentiation. Added actual logo/icons. Created this context file for cross-account persistence.

## Common Issues & Solutions
| Issue | Solution |
|-------|----------|
| yfinance returns empty data on Render | `download_ohlcv()` in stock_fetcher.py has Yahoo v8 API fallback |
| Portfolio shows "temporarily unavailable" | daily_job.py now falls back to hardcoded `USER_MF_HOLDINGS` from config.py |
| Telegram message too long (>4096 chars) | `send_telegram_sync()` auto-splits into 4000-char chunks |
| Markdown rejected by Telegram | Falls back to plain text automatically |
| Render free tier goes to sleep | Keep-alive self-ping every 10 minutes in main.py |
| SSL errors on macOS | `ssl._create_default_https_context = ssl._create_unverified_context` |

## Environment Variables Required on Render
- `DATABASE_URL` — Neon.tech PostgreSQL connection string
- `TELEGRAM_BOT_TOKEN` — from @BotFather
- `TELEGRAM_CHAT_ID` — Sai's chat ID
- `GEMINI_API_KEY` — Google AI Studio key for Gemini 2.5 Flash
- `RENDER_EXTERNAL_URL` — auto-set by Render

---

*Last updated: May 5, 2026*
*Maintained by: Agent Alpha (AI) & Sai*
