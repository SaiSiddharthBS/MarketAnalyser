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
    UI["Obsidian Glass UI (PWA, 60FPS Charts)"] -->|HTTPS / REST| API["FastAPI Backend (Uvicorn Asynchronous)"]
    API --> Quant["Quant Engine (15-Model Ensemble & HMM)"]
    API --> Arena["Paper Trading Arena (10L Initial Capital)"]
    API --> DB[("Neon PostgreSQL & SQLite Cache")]
    Quant --> TG["Telegram Bot (Live Signal Execution)"]
    Arena --> TG
    DataFetch["yfinance / FRED"] --> Quant
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

The **Paper Trading Arena** is where models prove their worth. Rigorously stress-tested, the Arena operates with a strict **₹10 Lakh (`₹1,000,000`) Base Capital**.

*   **Real-time Ledger:** Deducts margin, tracks open P&L, and accounts for brokerage and slippage. We rigidly reset the capital logic to 10L to preserve mathematical integrity and prevent long/short miscalculations.
*   **Dynamic Margin Calculation:** Ensures that the 10L baseline is protected, utilizing Kelly Criterion to size bets appropriately without blowing up the account.
*   **Weekend Staleness Architecture:** Upgraded to natively handle 96-hour data staleness thresholds to gracefully maneuver over weekends without triggering false "stale data" vetos.

---

### 3. The 12-Rule Hard Veto Firewall

Before a signal generated by the Ensemble hits the 10L Arena, it is subjected to a **Zero-Trust Veto**:

```mermaid
flowchart LR
    Signal(Ensemble Signal) --> Veto{12-Rule Veto Firewall}
    Veto -->|"Pledging > 40%"| Block(STAND ASIDE)
    Veto -->|"VIX Spike"| Block
    Veto -->|"Earnings in 3 Days"| Block
    Veto -->|"FII Heavy Selling"| Block
    Veto -->|"HMM Crisis State"| Block
    Veto -->|"All Rules Pass"| Exec(EXECUTE IN ARENA)
```

---

### 4. Telegram Bot Integration

Immediate, asynchronous notification is a staple of a CEO-level system. The **Agent Alpha Telegram Bot** acts as the direct line of communication between the engine and the executive.
*   **Daily Executive Briefings:** Triggered at 8:00 AM IST.
*   **Live Execution Alerts:** Instant push notification when a position is opened or closed in the Arena.
*   **P&L Snapshots:** End-of-day ledger summaries of the 10L capital pool.

---

## 🧮 Quantitative Mathematics & Formulas

Agent Alpha relies on rigorous mathematical foundations for regime classification, volatility scaling, and position sizing.

### 1. Hidden Markov Model (HMM) Regime Classification
We model the market environment as a Hidden Markov Process to prevent lagging execution and whipsaws. The market state $\mathbf{X}_t$ is classified into one of 4 hidden states using a Gaussian HMM based on the observation vector:

$$ \mathbf{X}_t = \{ R_t, \sigma_{20}, \text{VIX}_t, \text{Breadth}_t, \Delta_{\text{EMA200}} \} $$

*   **$R_t$:** Daily logarithmic return.
*   **$\sigma_{20}$:** 20-day rolling standard deviation of returns.
*   **$\text{VIX}_t$:** India VIX closing value.
*   **$\text{Breadth}_t$:** Nifty 50 Advance-Decline Ratio.
*   **$\Delta_{\text{EMA200}}$:** Percentage distance from the 200-day Exponential Moving Average.

### 2. Average True Range (ATR) Volatility Sizing
Position size is dynamically adjusted so that the stop-loss distance equates to a maximum risk limit of $2\%$ of overall portfolio equity ($E$):

$$ \text{True Range (TR)} = \max(H - L, |H - C_{prev}|, |L - C_{prev}|) $$
$$ \text{ATR}_{14} = \frac{13 \times \text{ATR}_{prev} + \text{TR}}{14} $$
$$ \text{Stop Loss Distance} = 2 \times \text{ATR}_{14} $$
$$ \text{Position Value} = \frac{E \times 0.02}{\text{Stop Loss Distance} / \text{Price}} $$

*   **$E$:** Current Equity in the Paper Trading Arena (e.g., ₹10,000,000 base).
*   **$H, L, C_{prev}$:** High, Low, and Previous Close prices.

### 3. Kelly Criterion Position Scaling
To prevent over-leveraging and drawdowns, raw Kelly fractions ($K_{\text{raw}}$) are computed based on historical win rates ($W$) and profit factors ($R$):

$$ K_{\text{raw}} = W - \frac{1 - W}{R} $$

This fraction is scaled dynamically by the regime modifier ($M_{\text{regime}}$) and the global pre-market bias score ($B_{\text{global}}$):

$$ K_{\text{final}} = K_{\text{raw}} \times M_{\text{regime}} \times (1 + B_{\text{global}}) $$

*   **$W$:** Historical probability of a winning trade.
*   **$R$:** Ratio of average profit to average loss.
*   **$M_{\text{regime}}$:** Scaling multiplier based on the HMM State (e.g., $1.0$ for Low-Volatility Uptrend, $0.3$ for Low-Volatility Chop).

### 4. Statistical Arbitrage Pairs Trading (Z-Score)
Identifies highly cointegrated sector pairs (e.g., HDFCBANK vs. ICICIBANK) and calculates their spread:

$$ \text{Spread}_t = \ln(P_{A,t}) - \beta \ln(P_{B,t}) $$
$$ Z_t = \frac{\text{Spread}_t - \mu_{\text{spread}}}{\sigma_{\text{spread}}} $$

*   **$\beta$:** Hedge ratio computed via Ordinary Least Squares (OLS) regression.
*   **$\mu_{\text{spread}}, \sigma_{\text{spread}}$:** Rolling mean and standard deviation of the spread.
*   **Signal Trigger:** Executes a mean-reversion trade when $|Z_t| > 2$.

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
