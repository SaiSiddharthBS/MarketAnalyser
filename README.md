<div align="center">
  <img src="Agent%20Alpha%20Logo%20v2.png" alt="Agent Alpha Logo" width="150" />
  
  <h1><b style="color: #00FF88;">AGENT ALPHA v3.0</b> | <i>The Apex of Algorithmic Trading</i></h1>
  <p><b>Institutional-Grade Algorithmic Trading Core & Quantitative AI Ensemble Engine</b></p>

  <img src=".github/assets/agent_alpha_terminal_ui.png" alt="Agent Alpha Terminal UI" width="100%" style="border-radius: 12px; box-shadow: 0 4px 30px rgba(0,255,136,0.2); margin-top: 20px;" />

  <br><br>

  [![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
  [![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
  [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org/)
  [![XGBoost](https://img.shields.io/badge/XGBoost-FF9800?style=for-the-badge&logo=nvidia&logoColor=white)](https://xgboost.ai/)
  [![LightGBM](https://img.shields.io/badge/LightGBM-A6E3A1?style=for-the-badge&logo=cpu&logoColor=black)](https://github.com/microsoft/LightGBM)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
  [![Status](https://img.shields.io/badge/Status-Production_Live-success?style=for-the-badge)]()
</div>

<hr style="border: 1px solid rgba(255,255,255,0.1);">

## 📖 Executive Overview

**Agent Alpha** is not just an indicator; it is a **fully autonomous, highly scalable, and production-ready quantitative intelligence system** designed to outmaneuver the Indian Stock Market (Nifty 50 universe). Combining the bleeding edge of machine learning, statistical arbitrage, and a deeply optimized paper trading arena, Agent Alpha represents a CEO-level deployment of quantitative logic.

We threw out the idea of simple rule-based trading. Instead, we architected a **15-Model Machine Learning Ensemble** spanning tabular classifiers (like **XGBoost** and **LightGBM**), sequence-based neural networks, statistical arbitrage, and macro microstructure analysis.

With **Zero-Trust Capital Preservation Architecture**, every signal must survive a **4-State Hidden Markov Model (HMM) Regime Classifier**, navigate a ruthless **12-Rule Hard Veto Firewall**, and calculate its weight via **ATR & Kelly Criterion Position Sizing**. Everything is pushed to a Serverless Neon PostgreSQL instance, and execution reports are immediately dispatched via the **Agent Alpha Telegram Bot**.

---

## 🚀 The Agent Alpha Ecosystem Mindmap

```mermaid
mindmap
  root((Agent Alpha v3.0))
    Engine Core
      15-Model Ensemble
      XGBoost & LightGBM Classifiers
      Statistical Arbitrage
    Risk Management
      HMM Regime Classifier
      12-Rule Veto Firewall
      ATR Position Sizing
      Kelly Criterion Allocation
    Data & Infrastructure
      yfinance & FRED APIs
      Neon PostgreSQL
      SQLite Fast Cache
      Decoupled Cron Daemons
    Execution & Reporting
      Paper Trading Arena
      ₹10L Starting Capital
      Telegram Bot Alerts
      Obsidian Glass UI
```

---

## 🛠️ Complete Deployed Technology Stack & Block Diagram

Our stack is built on the principles of **Linear-style aesthetics, Glassmorphism, and GSAP-like smooth interfaces** for the frontend, coupled with an industrial-grade backend.

```mermaid
graph TD
    UI[Obsidian Glass UI<br/>(PWA, 60FPS Charts)] -->|HTTPS / REST| API(FastAPI Backend<br/>Uvicorn Asynchronous)
    API --> Quant[Quant Engine<br/>15-Model Ensemble & HMM]
    API --> Arena[Paper Trading Arena<br/>10L Initial Capital]
    API --> DB[(Neon PostgreSQL<br/>& SQLite Cache)]
    Quant --> TG[Telegram Bot<br/>Live Signal Execution]
    Arena --> TG
    DataFetch[yfinance / FRED] --> Quant
```

---

## 🧠 Core System Modules (Deep Dive)

### 1. The 15-Model Quantitative Ensemble Engine

At the heart of Agent Alpha lies a weighted voting ensemble that outputs a continuous directional bias. 

#### 🚀 Machine Learning Classifiers: XGBoost & LightGBM
*   **XGBoost Classifier:** Trained on historical OHLCV data using an advanced walk-forward cross-validation window. Emits probabilities for 3 classes: Up (>2% in 5 days), Down (<-2% in 5 days), and Flat.
*   **LightGBM Classifier:** Highly optimized, gradient-boosted decision tree layer natively handling complex engineered features (e.g. microstructure shadows, volume profiles).
*   **Lightweight Sequence Model & Short-Term MLP:** Temporal classifiers mimicking LSTM networks to capture cyclical wave patterns and order imbalances.

#### 📊 Microstructure & Statistical Arbitrage
*   **StatArb Pairs Trading:** Monitors highly cointegrated sector pairs.
*   **Smart Money / VPOC:** Scans intraday data for high-density institutional accumulation block trades.

---

### 2. The Paper Trading Arena (The 10L Crucible)

The **Paper Trading Arena** is where models prove their worth. Recently reset and rigorously stress-tested, the Arena operates with a strict **₹10 Lakh (`₹1,000,000`) Base Capital**.

*   **Real-time Ledger:** Deducts margin, tracks open P&L, and accounts for brokerage and slippage.
*   **Dynamic Margin Calculation:** Ensures that the 10L baseline is protected, utilizing Kelly Criterion to size bets appropriately without blowing up the account.
*   **Weekend Staleness Fix:** Upgraded to natively handle 96-hour data staleness thresholds to gracefully maneuver over weekends without triggering false "stale data" vetos.

---

### 3. The 12-Rule Hard Veto Firewall

Before a signal generated by the Ensemble hits the 10L Arena, it is subjected to a **Zero-Trust Veto**:

```mermaid
flowchart LR
    Signal(Ensemble Signal) --> Veto{12-Rule Veto Firewall}
    Veto -->|Pledging > 40%| Block(STAND ASIDE)
    Veto -->|VIX Spike| Block
    Veto -->|Earnings in 3 Days| Block
    Veto -->|FII Heavy Selling| Block
    Veto -->|HMM Crisis State| Block
    Veto -->|All Rules Pass| Exec(EXECUTE IN ARENA)
```

---

### 4. Telegram Bot Integration

Immediate, asynchronous notification is a staple of a CEO-level system. The **Agent Alpha Telegram Bot** acts as the direct line of communication between the engine and the executive.
*   **Daily Executive Briefings:** Triggered at 8:00 AM IST.
*   **Live Execution Alerts:** Instant push notification when a position is opened or closed in the Arena.
*   **P&L Snapshots:** End-of-day ledger summaries of the 10L capital pool.

---

## 📅 Deployment Roadmap & Changelog (April 30, 2026 – May 24, 2026)

This project has evolved at breakneck speed. Here is the unedited, comprehensive ledger of deployment milestones achieved over the last month:

### **Phase 1: Foundation & Modeling (April 30 - May 7)**
*   **April 30:** Initial scaffolding of the FastAPI server and Uvicorn asynchronous event loops.
*   **May 2:** Integrated `yfinance` for Nifty 50 historical data collection. Built the SQLite caching layer.
*   **May 4:** **XGBoost** and **LightGBM** models integrated and backtested with walk-forward validation.
*   **May 7:** 12-Rule Hard Veto Firewall conceptualized. Data structure modeled for Neon PostgreSQL deployment.

### **Phase 2: The UI & The Arena (May 8 - May 15)**
*   **May 8:** The **Obsidian Glass UI** was born. Implemented custom glassmorphism CSS, bypassing heavy CSS frameworks for pure Vanilla performance.
*   **May 11:** TradingView lightweight charts embedded for 60FPS fluid rendering of stock prices.
*   **May 13:** The **Paper Trading Arena** was initialized. Base capital set to **₹10,000,000** (10 Lakhs).
*   **May 15:** Integrated the **Telegram Bot API** for live asynchronous notifications of Arena executions.

### **Phase 3: Refinement, HMM & Math Fixes (May 16 - May 22)**
*   **May 16:** **Hidden Markov Model (HMM)** integrated to define the 4-State market regimes.
*   **May 19:** Critical fix: Resolved a long/short mathematics misunderstanding in the Arena. The ledger was fully reset back to a clean **10L** to ensure mathematical integrity.
*   **May 22:** Engineered the ATR Volatility and Kelly Criterion Position Sizing equations to dynamically scale risk.

### **Phase 4: CEO-Level Polish & System Resilience (May 23 - May 24)**
*   **May 23:** Detected weekend data staleness glitch. System was rejecting valid Sunday/Monday signals due to a 48h limit. Upgraded `max_staleness_hours` to 96 to ensure robust cross-weekend operations.
*   **May 24 (Today):** The **Ultimate Deployment**. Codebase restructured, terminal UI mockups generated, mind maps embedded, and README.md upgraded to an industrial, Awwwards-worthy standard.

---

## ⚡ Deployment & Local Setup

Agent Alpha is cloud-native, containerized, and configured for immediate execution.

### 1. Clone & Environment Configuration
```bash
git clone https://github.com/SaiSiddharthBS/MarketAnalyser.git
cd MarketAnalyser
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment Variables (.env)
```env
DATABASE_URL=postgresql://user:pass@ep-host.neon.tech/neondb?sslmode=require
TELEGRAM_BOT_TOKEN=your_telegram_token
TELEGRAM_CHAT_ID=your_chat_id
GEMINI_API_KEY=your_gemini_api_key
```

### 3. Ignition
```bash
# Start FastAPI backend (serves Obsidian Glass UI on http://localhost:8000)
uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Launch background execution clock
python backend/scheduler.py
```

<br>
<div align="center">
  <i>"The future of finance is not predicted. It is computed."</i><br/>
  <b>— Agent Alpha v3.0 Core</b>
</div>
