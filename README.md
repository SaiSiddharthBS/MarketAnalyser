<div align="center">
  <img src=".github/assets/hero_banner.png" alt="Agent Alpha Hero Banner" width="100%">
  
  <h1><b>AGENT ALPHA</b></h1>
  <p><b>Institutional-Grade Algorithmic Trading & AI Ensemble Engine</b></p>
  
  [![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
  [![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
  [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
  [![Status](https://img.shields.io/badge/Status-Production_Live-success?style=for-the-badge)]()
</div>

<br/>

## 🦅 Executive Summary
**Agent Alpha** is a completely autonomous, serverless-ready quantitative trading intelligence. Built from the ground up to rival institutional quant desks, it relies on a sophisticated **15-Model Machine Learning Ensemble** intersecting with **Hidden Markov Models (HMM)** to detect market regimes, dynamically sizing positions while prioritizing capital preservation.

Every signal generated is backtested instantly via Walk-Forward Validation and executed dynamically in a live Paper Trading Arena—all piped directly to the CEO’s Telegram for oversight.

---

## 🔥 Key Architectures (Deployed April 30 - May 24, 2026)

### 1. The 15-Model Institutional Ensemble (Powered by XGBoost & LightGBM)
Rather than relying on singular technical indicators, Agent Alpha aggregates 15 discrete models across 4 unique alpha-generating dimensions, heavily anchored by **XGBoost** and **LightGBM** gradient boosting classifiers for state-of-the-art predictive accuracy:
*   **Technical Matrix:** Moving Average Ribbons (KAMA, EMA), RSI bounds, ATR Volatility.
*   **Momentum Matrix:** MACD Histograms, Rate of Change (ROC), On-Balance Volume (OBV).
*   **Transformer AI Patterns:** Deep learning integration for recognizing double-tops, ascending triangles, and structural exhaustion.
*   **Macro & Regime Bias:** Broad market tailwinds, VIX-adjusted scaling, and Nifty 50 correlation mapping.

### 2. Capital Preservation & HMM Regime Detection
The system is built on one simple rule: *Survival over outperformance.*
*   **HMM Classifier:** Constantly analyzes the Nifty 50 to classify the environment into states like `High Volatility Chop`, `Mean Reversion`, or `Trending Bull`.
*   **Capital Preservation Veto:** If the market enters a `Chop` regime, the internal `DataValidator` enforces a rigid capital preservation policy. The system will aggressively veto (reject) any trade that does not exhibit at least `1.4x` Relative Volume (RVOL) or strong Multi-Timeframe (MTF) alignment.

### 3. The Paper Trading Arena
A fully automated execution pipeline running on a virtual **₹1,000,000 (10 Lakh)** portfolio.
*   **Dynamic Position Sizing:** Automatically calculates position sizes based on a strict `2% Risk Limit` per trade, utilizing the stock's ATR (Average True Range).
*   **Live Equity Curve:** Tracks Mark-to-Market (MTM) daily equity against the Nifty 50 benchmark.
*   **Postgres State Management:** Entire portfolio state is persisted securely in a Neon Serverless PostgreSQL database with connection pooling.

### 4. Data Immune System
Agent Alpha employs a ruthless `DataValidator` that sanitizes all incoming `yfinance` and macroeconomic data.
*   **Staleness Checks:** Actively drops any stock data older than **96 hours** to prevent weekend-glitches and split-adjustment anomalies.
*   **Null Overrides:** Purges incomplete OHLCV candles to ensure the ML ensemble never hallucinates on broken data.

### 5. Multi-Timeframe (MTF) Alignment
Alpha generation isn't just about the daily candle. The engine maps Daily momentum against Weekly trends. 
*   **Headwind (Conflict):** If the Daily chart signals Long, but the Weekly trend is Bearish, the stock is downgraded to a `🟡 Watch (Forming)` label.
*   **Tailwind (Alignment):** If both timeframes align, the stock is upgraded to a `💎 Dip Opportunity` or `🚀 Early Breakout`.

### 6. Obsidian Glass UI & Visual Analytics
The frontend is a bespoke **Progressive Web App (PWA)** utilizing a jaw-dropping *Obsidian Glassmorphism* aesthetic.
*   **Lightweight Charts Integration:** Rendering thousands of data points at 60FPS using TradingView's standalone library.
*   **Real-time Alerts:** Integrated with Telegram APIs to ping executions, daily summaries, and market anomalies straight to your phone.

---

## 🏗️ System Architecture

Agent Alpha is fully containerized. A Dockerfile orchestrates the FastApi monolithic core, while a separate background cron job handles market-close scraping.

> **For complete, full-scale Mermaid flowcharts, block diagrams, and obsidian mindmaps of our data pipeline, please view the [ARCHITECTURE.md](./ARCHITECTURE.md) document.**

---

## ⚡ Deployment & Local Setup

Agent Alpha is cloud-native and ready for Render/AWS. To run locally:

### 1. Clone & Environment
```bash
git clone https://github.com/SaiSiddharthBS/MarketAnalyser.git
cd MarketAnalyser
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment Variables
Create a `.env` file in the root directory:
```env
DATABASE_URL=postgresql://user:pass@ep-host.neon.tech/neondb?sslmode=require
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
FRED_API_KEY=your_fred_key
```

### 3. Run the Core Platform
Start the FastAPI backend (this will also serve the Obsidian Glass UI on the root path):
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```
Visit `http://localhost:8000` to access the trading terminal.

### 4. Run the Background Scheduler
In a separate terminal, launch the daemon that handles Overnight Intel and Daily Arena Execution:
```bash
python backend/scheduler.py
```

---

<div align="center">
  <i>"The future of finance is not predicted. It is computed."</i><br/>
  <b>— Agent Alpha v3.0</b>
</div>
