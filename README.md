<div align="center">
  <img src=".github/assets/hero_banner.png" alt="Agent Alpha Hero Banner" width="100%">
  
  <h1><b>🦅 AGENT ALPHA v3.0</b></h1>
  <p><b>Institutional-Grade Algorithmic Trading Core & Quantitative AI Ensemble Engine</b></p>
  
  [![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
  [![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
  [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org/)
  [![LightGBM](https://img.shields.io/badge/LightGBM-A6E3A1?style=for-the-badge&logo=cpu&logoColor=black)](https://github.com/microsoft/LightGBM)
  [![XGBoost](https://img.shields.io/badge/XGBoost-FF9800?style=for-the-badge&logo=nvidia&logoColor=white)](https://xgboost.ai/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
  [![Status](https://img.shields.io/badge/Status-Production_Live-success?style=for-the-badge)]()
</div>

---

## 📖 Executive Overview

**Agent Alpha** is an autonomous, production-grade quantitative intelligence system built to analyze, model, and execute equity swing strategies on the Indian Stock Market (Nifty 50 universe). 

Rather than relying on singular technical indicators or fragile single-model predictors, Agent Alpha uses a **15-Model Machine Learning Ensemble** spanning tabular classifiers, sequence-based neural networks, statistical arbitrage, and microstructure analysis. 

The system operates with a **Zero-Trust Capital Preservation Architecture**: every predictive signal is strictly filtered by a **4-State Hidden Markov Model (HMM) Regime Classifier**, audited by a **12-Rule Hard Veto Firewall**, optimized using **Average True Range (ATR) & Kelly Criterion Position Sizing**, and logged securely to a cloud-serverless PostgreSQL cluster.

---

## 🛠️ Complete Deployed Technology Stack

```
   ┌─────────────────────────────────────────────────────────────┐
   │                     OBSIDIAN GLASS UI                       │
   │      - HTML5 Semantic Document Structure                    │
   │      - Custom Vanilla CSS Glassmorphic Layouts               │
   │      - TradingView Standalone Lightweight Charts (60 FPS)   │
   │      - Progressive Web App (PWA) Offline-Ready Service      │
   └──────────────────────────────┬──────────────────────────────┘
                                  │ (RESTful JSON / HTTPS)
                                  ▼
   ┌─────────────────────────────────────────────────────────────┐
   │                   FastAPI BACKEND ENGINE                    │
   │      - Uvicorn Asynchronous Concurrency Server              │
   │      - Threaded Postgres Connection Pooling                 │
   │      - Decoupled Overnight Daemon & System Scheduler         │
   └──────────────────────────────┬──────────────────────────────┘
                                  │
         ┌────────────────────────┴────────────────────────┐
         ▼                                                 ▼
┌────────────────────────────────┐                ┌────────────────────────────────┐
│      QUANTITATIVE ENGINE       │                │      DATA & INFRASTRUCTURE     │
│ - 15-Model Ensemble Voting     │                │ - Serverless Neon PostgreSQL   │
│ - HMM Regime Classifier        │                │ - Local SQLite Performance Cache│
│ - 12-Rule Hard Veto Firewall   │                │ - yfinance API Data Collector  │
│ - ATR & Kelly Position Sizing  │                │ - FRED Macroeconomic Engine    │
│ - StatArb Pairs Trading        │                │ - Telegram Bot Notification API│
└────────────────────────────────┘                └────────────────────────────────┘
```

---

## 🧠 Core System Modules (Detailed Specification)

### 1. The 15-Model Quantitative Ensemble Engine

The core predictive capability is structured as a weighted voting ensemble. Each model emits a continuous directional bias score between `-1.0` (Strong Sell) and `+1.0` (Strong Buy), which is dynamically weighted based on the active market regime.

```
       ┌─────────────────────────────────────────────────────────────┐
       │                15-MODEL QUANT ENSEMBLE                      │
       └──────┬──────────────┬──────────────┬──────────────┬─────────┘
              │              │              │              │
              ▼              ▼              ▼              ▼
         ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
         │ TECHNICAL│   │ MOMENTUM │   │ MACHINE  │   │ STAT-ARB │
         │ MATRIX   │   │ MATRIX   │   │ LEARNING │   │ & FLOW   │
         └──────────┘   └──────────┘   └──────────┘   └──────────┘
```

#### A. Technical Matrix (4 Models)
1.  **Moving Average Envelope (KAMA/EMA):** Maps multi-day Kaufmans Adaptive Moving Average (KAMA) speed against exponential moving averages (EMA 20, 50, 200) to isolate price/trend divergence.
2.  **Relative Strength Index (RSI-14):** Evaluates momentum exhaustion, capping thresholds based on market regime to prevent buying overextended breakouts during range-bound regimes.
3.  **Average True Range (ATR) Volatility:** Measures historical price contraction and expansion cycles.
4.  **Bollinger Bands (BB Width / Percentile):** Calculates standard deviation bands to locate volatility squeeze anomalies.

#### B. Momentum Matrix (3 Models)
5.  **MACD Histogram Directionality:** Traces the acceleration or deceleration of daily trend speed.
6.  **Rate of Change (ROC-10):** Measures pure percentage price velocity over rolling 10-day periods.
7.  **On-Balance Volume (OBV):** Evaluates volume flows to ensure price moves are confirmed by institutional participation.

#### C. Machine Learning & Neural Network Layer (4 Models)
8.  **XGBoost Classifier:** Trained on historical OHLCV data using a walk-forward cross-validation window. Emits probabilities for 3 classes: Up (>2% in 5 days), Down (<-2% in 5 days), and Flat.
9.  **LightGBM Classifier:** Used as a highly optimized, gradient-boosted decision tree layer that natively handles complex engineered features (e.g. microstructure shadows, volume profiles).
10. **Lightweight Sequence Model:** A CPU-optimized temporal classifier mimicking LSTM network structures. Processes a 60-day sliding window of sequence returns to capture cyclical wave patterns.
11. **Short-Term Multilayer Perceptron (MLP):** A multilayer neural network mapping short-term velocity (1-3 days) to predict near-term order imbalances.

#### D. Microstructure, Flow & Statistical Arbitrage (4 Models)
12. **Smart Money / Volume Point of Control (VPOC):** Scans intraday data to locate high-density institutional accumulation block trades (Demand vs. Supply Blocks).
13. **Statistical Arbitrage (Pairs Trading Z-Score):** Monitors highly cointegrated sector pairs (e.g., HDFCBANK vs. ICICIBANK, TCS vs. INFY) and calculates their log-spread Z-score. Generates mean-reversion signals when the spread exceeds $\pm2$ standard deviations.
14. **Institutional Flow (FII/DII net trend):** Tracks foreign and domestic institutional money flows into the Indian cash market.
15. **Options Flow (Put-Call Ratio):** Analyzes open interest across the options chain to detect options market sentiment.

---

### 2. Hidden Markov Model (HMM) Regime Classifier

Standard rule-based trend indicators suffer from lagging execution and severe whipsaws. Agent Alpha classifies Nifty 50 volatility and breadth into **4 hidden states** using a Gaussian Hidden Markov Model:

$$\mathbf{X}_t = \{R_t, \sigma_{20}, \text{VIX}_t, \text{Breadth}_t, \Delta_{\text{EMA200}}\}$$

*   **State 1: Low-Volatility Uptrend (Home Turf)**
    *   *Characteristics:* Steady returns, VIX $<15$, price well above 200 EMA.
    *   *System Action:* Full allocation limits enabled; momentum strategies prioritized.
*   **State 2: High-Volatility Uptrend (Cautious Bull)**
    *   *Characteristics:* Rising returns but expanding daily ranges, VIX $15-20$.
    *   *System Action:* Sizing scaled to `0.6x` of baseline Kelly allocation.
*   **State 3: Low-Volatility Chop (Stand Aside)**
    *   *Characteristics:* Flattish returns, range-bound index, sector rotation.
    *   *System Action:* Momentum models disabled; reversion models enabled; sizing capped to `0.3x` Kelly.
*   **State 4: Systemic Crisis (Survival Mode)**
    *   *Characteristics:* Sharp negative returns, VIX $>25$ (or spiking $>30\%$ in 5 days), price below 200 EMA.
    *   *System Action:* Stand-aside. Suppress all new BUY signals. Max capital preservation.

```mermaid
stateDiagram-v2
    [*] --> LowVolUptrend: Market Open
    LowVolUptrend --> HighVolUptrend: Volatility Expands (VIX > 15)
    HighVolUptrend --> LowVolChop: Momentum Fades
    LowVolChop --> Crisis: Sharp Drop (VIX > 25)
    Crisis --> LowVolUptrend: Institutional Accumulation
```

---

### 3. The 12-Rule Hard Veto Firewall

Before any signal generated by the Ensemble is executed in the paper trading database, it must pass through a strict **Hard Veto Firewall**. If **any** of the following rules fire, the signal is overridden and forced to `STAND ASIDE` or `LIQUIDATE`:

```
                    Ensemble BUY Signal Generated
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │ 12-RULE VETO FIREWALL │
                     └───────────┬───────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
       [ANY Rule Fails]                 [ALL Rules Pass]
                 │                               │
                 ▼                               ▼
        Signal Overridden               Approved for Execution
        "STAND ASIDE"                   "OPEN PAPER POSITION"
```

1.  **Promoter Pledging Cap:** Block buy signals if promoter pledging exceeds `40%` and is expanding quarter-on-quarter.
2.  **Pledging Velocity Check:** Veto trades if pledging increases by $>10\%$ in a single financial quarter.
3.  **Earnings Blackout Margin:** Prevent purchases if the company has an earnings announcement scheduled within the next `3 trading days`.
4.  **Lower Circuit History:** Block stocks that have touched their daily lower circuit limit within the last `10 trading days`.
5.  **Regulatory Measure List (ASM/ESM):** Suppress buying if the stock is placed under SEBI's Additional or Enhanced Surveillance Measure frameworks.
6.  **SEBI Investigation Flag:** Immediate block if the company is facing an active regulatory audit or SEBI investigation.
7.  **Credit Downgrade Velocity:** Block stocks experiencing a credit rating downgrade of `2 or more notches` within a 90-day window.
8.  **Extreme Volatility + Short Buildup:** Block trades if options Implied Volatility (IV) percentile exceeds `85` while the open interest indicates active Short Buildup.
9.  **Institutional Expatriation Veto:** Veto buying if daily FII net selling exceeds `₹5000 Crore` on the preceding day.
10. **Systemic Crisis Veto:** Block all buys if the HMM regime transitions to `CRISIS`.
11. **Global Pre-Market Gap down:** Suppress buying if SGX Nifty/Gift Nifty indicates an overnight gap-down of $>1.5\%$.
12. **Extreme VIX Spike:** Halts all buying if VIX surges $>30\%$ in a 5-day window.

---

### 4. Position Sizing & Portfolio Optimization Math

#### Average True Range (ATR) Volatility Sizing
Position size is dynamically adjusted so that the stop-loss distance equates to a maximum risk limit of $2\%$ of overall portfolio equity ($E$):

$$\text{Stop Loss Distance} = 2 \times \text{ATR}_{14}$$

$$\text{Position Value} = \frac{E \times 0.02}{\text{Stop Loss Distance} / \text{Price}}$$

#### Kelly Criterion Scaling
To prevent over-leveraging and drawdowns, raw Kelly fractions ($K_{\text{raw}}$) are computed based on historical win rates ($W$) and profit factors ($R$):

$$K_{\text{raw}} = W - \frac{1 - W}{R}$$

This fraction is scaled dynamically by the regime modifier ($M_{\text{regime}}$) and the global pre-market bias score ($B_{\text{global}}$):

$$K_{\text{final}} = K_{\text{raw}} \times M_{\text{regime}} \times (1 + B_{\text{global}})$$

---

## 💻 System Execution Pipelines

### Pre-Market Intelligence Pipeline (Daily 8:00 AM IST)

```mermaid
sequenceDiagram
    participant Scheduler as Cron Daemon
    participant Global as Global Asset Scanner
    participant Regime as HMM Engine
    participant DB as Postgres Cache
    participant TG as Telegram API

    Scheduler->>Global: Trigger Overnight Scan
    Global->>Global: Fetch S&P500, IndiaVIX, SGX, Gold, Bonds
    Global->>Regime: Run Regime Classification
    Regime-->>Global: Returns HMM State & Bias
    Global->>DB: Log Daily Market Regime
    Global->>TG: Transmit CEO Executive Briefing
```

### Paper Trading Arena Pipeline (Daily 3:45 PM IST)

```mermaid
sequenceDiagram
    participant Scheduler as System Clock
    participant Ensemble as 15-Model Ensemble
    participant Veto as Veto Firewall
    participant Arena as Paper Arena Bot
    participant DB as Neon Postgres DB
    participant TG as Telegram Bot

    Scheduler->>Ensemble: Run Universe Screener
    Ensemble->>Veto: Audit High-Conviction BUY/SELL
    Veto-->>Ensemble: Filtered/Approved Signals
    Ensemble->>Arena: Trigger Execution Signals
    Arena->>DB: Read Cash Balance (₹10 Lakh Base)
    Arena->>Arena: Run Sizing & Margin Math
    Arena->>DB: Open/Close Trades & Update Snapshots
    Arena->>TG: Send Transaction Log & Equity Curves
```

---

## ⚡ Deployment & Local Setup

Agent Alpha is cloud-native, containerized, and configured for immediate cloud deployment.

### 1. Clone & Environment Configuration
```bash
git clone https://github.com/SaiSiddharthBS/MarketAnalyser.git
cd MarketAnalyser
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment Variables (.env)
Create a `.env` file in the root directory:
```env
DATABASE_URL=postgresql://user:pass@ep-host.neon.tech/neondb?sslmode=require
TELEGRAM_BOT_TOKEN=your_telegram_token
TELEGRAM_CHAT_ID=your_chat_id
GEMINI_API_KEY=your_gemini_api_key
```

### 3. Run the Execution Server
```bash
# Start FastAPI backend (serves Obsidian Glass UI on http://localhost:8000)
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### 4. Run the Background Scheduler Daemon
```bash
# Launches the background execution clock for pre-market and market-close jobs
python backend/scheduler.py
```

---

<div align="center">
  <i>"The future of finance is not predicted. It is computed."</i><br/>
  <b>— Agent Alpha v3.0 Core</b>
</div>
