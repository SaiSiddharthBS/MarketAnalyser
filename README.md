<div align="center">
  <img src="Agent%20Alpha%20Logo%20v2.png" alt="Agent Alpha Logo" width="150" />
  
  <h1><b style="color: #00FF88;">AGENT ALPHA</b></h1>
  <p><b>Institutional-Grade Algorithmic Trading Core & Quantitative AI Ensemble Engine</b></p>

  <img src=".github/assets/agent_alpha_terminal_ui.png" alt="Agent Alpha Terminal UI" width="100%" style="border-radius: 12px; box-shadow: 0 4px 30px rgba(0,255,136,0.2); margin-top: 20px;" />

  <br><br>

  [![CI](https://github.com/SaiSiddharthBS/MarketAnalyser/actions/workflows/main.yml/badge.svg)](https://github.com/SaiSiddharthBS/MarketAnalyser/actions)
  ![Last Commit](https://img.shields.io/github/last-commit/SaiSiddharthBS/MarketAnalyser?style=for-the-badge&color=00FF88)
  ![Repo Size](https://img.shields.io/github/repo-size/SaiSiddharthBS/MarketAnalyser?style=for-the-badge&color=38bdf8)
  <br>
  [![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
  [![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
  [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org/)
  [![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
  [![XGBoost](https://img.shields.io/badge/XGBoost-FF9800?style=for-the-badge&logo=nvidia&logoColor=white)](https://xgboost.ai/)
  [![Ollama](https://img.shields.io/badge/Ollama-LLaMA_3.3_70B-000000?style=for-the-badge&logo=meta&logoColor=white)](https://ollama.ai/)
  [![Status](https://img.shields.io/badge/Status-Production_Live-success?style=for-the-badge)]()
</div>

<hr style="border: 1px solid rgba(255,255,255,0.1);">

## 📑 Table of Contents
- [Executive Overview](#-executive-overview)
- [Enterprise Feature Suite](#-enterprise-feature-suite-ui-vs-autonomous-engine)
- [Multi-Horizon Trading Expertise](#-multi-horizon-trading-expertise)
- [Why Agent Alpha?](#-why-agent-alpha)
- [Architecture & Topology](#-hardware-architecture-the-dual-node-setup)
- [15-Model Ensemble & Deep Dives](#-core-system-modules--deep-dives)
- [Mathematical Foundations](#-mathematical-models--algorithmic-foundations)
- [Deployment Topology](#-dockerization--cloud-deployment-topology)

---

## 📖 Executive Overview

**Agent Alpha** is not just an indicator; it is a **fully autonomous, highly scalable, and production-ready quantitative intelligence system** designed to outmaneuver the Indian Stock Market (Nifty 50 universe). Combining the bleeding edge of machine learning, statistical arbitrage, and a deeply optimized paper trading arena, Agent Alpha represents a CEO-level deployment of quantitative logic.

We threw out the idea of simple rule-based trading. Instead, we architected a **15-Model Machine Learning Ensemble** spanning tabular classifiers (like **XGBoost** and **LightGBM**), sequence-based neural networks, statistical arbitrage, and macro microstructure analysis.

With **Zero-Trust Capital Preservation Architecture**, every signal must survive a **4-State Hidden Markov Model (HMM) Regime Classifier**, navigate a ruthless **12-Rule Hard Veto Firewall**, and calculate its weight via **ATR & Kelly Criterion Position Sizing**. 

---

## 🔥 Enterprise Feature Suite: UI vs. Autonomous Engine

### 🧠 Autonomous Execution & AI
*   **Zero-Latency Signal Generation:** Engine processes OHLCV ticks, calculates 15 model vectors, and generates a unified bias in `<400ms`.
*   **LLM Catalyst Engine (Ollama + LLaMA 3.3 70B Versatile):** Natively ingests live news headlines and complex corporate SEC/NSE filings. Instead of relying on generic cloud APIs, it routes sentiment analysis and financial parsing through a highly-capable, locally-hosted **LLaMA 3.3 70B Versatile** model via **Ollama**, ensuring zero data leakage, unthrottled inference speed, and institutional-grade natural language reasoning.
*   **Walk-Forward ML Optimization:** Models never curve-fit. They are trained sequentially on rolling windows to guarantee out-of-sample robustness.

### 🛡️ Institutional Risk Management
*   **Dynamic Kelly Criterion:** Position sizing isn't guessed. It is mathematically derived from the historical win-rate and profit factor of the active HMM regime.
*   **12-Rule Hard Veto Firewall:** A ruthless zero-trust layer that blocks trades during VIX spikes, impending earnings reports, or heavy FII selling.
*   **Dynamic Correlation Heatmap:** Actively calculates Pearson correlation across the portfolio to prevent localized sector beta-collapse.

### ⚡ The Obsidian Glass Executive UI
*   **Terminal Noir Aesthetic:** A gorgeous, hardware-accelerated dark mode PWA featuring Glassmorphism, tailored for the CEO's secondary monitor.
*   **60FPS WebSockets:** Live execution LED pulses, real-time P&L tickers, and portfolio drawdown metrics streamed directly from the Python backend.
*   **Live Telegram Sub-System:** Instant push notifications for every Ensemble Vote, Firewall Veto, and executed trade directly to your phone.

---

## ⏱️ Multi-Horizon Trading Expertise

Agent Alpha dynamically scales its analysis across three distinct temporal horizons, ensuring alpha extraction regardless of market speed.

1. **Intraday Microstructure (High-Frequency Context):**
   Scans the first 45 minutes of the trading session for Smart Money block orders and Volume Point of Control (VPOC) migrations to gauge institutional sentiment before executing swing trades.
2. **Short-Term Swing & Momentum (The Core Engine):**
   Optimized for a 3-to-15 day holding period. Leverages the LightGBM classifiers and ROC/MACD momentum matrices to ride the primary thrust of the prevailing market wave, minimizing overnight gap risk while capturing maximum velocity.
3. **Long-Term Macro (Regime Filtering):**
   Monitors the 200-day EMA, FII/DII institutional flow, and India VIX to dictate the overarching **Hidden Markov Model (HMM) State**. Prevents the system from buying long-term secular downtrends or systemic crises.

---

## 🆚 Why Agent Alpha?

| Capability | Generic Trading Bot | Agent Alpha |
|:--|:--|:--|
| **Signal Generation** | Single indicator (e.g., RSI crossover) | 15-model weighted ensemble |
| **Regime Awareness** | None (trades blindly in all conditions) | 4-state Hidden Markov Model |
| **Risk Firewall** | Basic static stop-loss | 12-rule zero-trust veto |
| **Position Sizing** | Fixed lots / constant capital | ATR + Kelly Criterion scaling |
| **Database Architecture**| Local JSON / SQLite | Neon PostgreSQL Serverless DB |
| **AI Integration** | Cloud API calls (OpenAI) | Local LLaMA 3.3 70B (zero data leakage) |
| **Infrastructure** | Single python script | Dual-node Docker cluster + shell scripts |

---

## 🚀 The Agent Alpha Ecosystem Mindmap

> 🌐 **[Launch Interactive Architecture Explorer →](https://SaiSiddharthBS.github.io/MarketAnalyser/react_terminal/index.html)**

<div align="center">
  <img src=".github/assets/diagrams/mindmap_glowing.png" alt="Agent Alpha Ecosystem Mindmap" width="100%" style="border-radius: 12px; box-shadow: 0 4px 30px rgba(0,255,136,0.15);" />
</div>

---

## 🏗️ Hardware Architecture: The Dual-Node Setup

Agent Alpha operates on a resilient, distributed physical architecture split across two synchronized machines. This ensures absolute separation of heavy quantitative compute processes and the executive visualization dashboard.

<div align="center">
  <img src=".github/assets/diagrams/architecture.png" alt="Dual-Node Hardware Architecture" width="100%" style="border-radius: 12px; box-shadow: 0 4px 30px rgba(0,229,255,0.15);" />
</div>

**Node 1 (Primary Executive Station - MacBook Pro):** The visualization and development terminal. The CEO interacts with the system here via the stunning Obsidian Glass UI. Development, testing, and UI overhauls are tested natively here.
**Node 2 (Sentinel Execution Node - Always-On Windows):** The absolute core of the operation. This secondary node runs the `docker-compose` stack containing the FastAPI backend, Neon DB links, Cron daemons, ML models, and the localized **Ollama (LLaMA 3.3 70B)** engine. Because Node 2 is "Always-On", the 8:00 AM pre-market scans and 3:45 PM execution cron-jobs trigger relentlessly without fail. Deployment from MacBook to Node 2 is handled via our custom `deploy_to_dell.sh` CI/CD script.

---

## 🧠 Core System Modules & Deep Dives

### 1. The 15-Model Quantitative Ensemble Engine

At the heart of Agent Alpha lies a weighted voting ensemble that outputs a continuous directional bias. Rather than relying on a single point of failure, the engine synthesizes signals from 15 distinct, uncorrelated models across 4 unique matrices.

<div align="center">
  <img src=".github/assets/diagrams/ensemble.png" alt="15-Model Quantitative Ensemble Engine" width="100%" style="border-radius: 12px; box-shadow: 0 4px 30px rgba(0,255,136,0.15);" />
</div>

#### 📐 A. Technical Matrix (4 Models)
<details>
<summary><b>Click to expand Technical Models</b></summary>
1.  **Kaufmans Adaptive Moving Average (KAMA/EMA):** Measures price divergence against a multi-day EMA baseline, filtering out market "noise" during high volatility.
2.  **Regime-Adjusted RSI-14:** A momentum oscillator dynamically capped by the active HMM state to prevent buying false breakouts in range-bound regimes.
3.  **ATR Volatility Expansion:** Triggers when severe price contractions (coiling) resolve into aggressive directional volatility expansions.
4.  **Bollinger Squeeze Percentile:** Locates statistical standard-deviation squeeze anomalies right before a trend accelerates.
</details>

#### 🌊 B. Momentum Matrix (3 Models)
<details>
<summary><b>Click to expand Momentum Models</b></summary>
5.  **MACD Histogram Acceleration:** Measures the second derivative (acceleration/deceleration) of the short-term trend rather than just the direction.
6.  **Rate of Change (ROC-10):** Measures pure unadulterated percentage price velocity over a rolling 10-day period.
7.  **On-Balance Volume (OBV):** Ensures price breakouts are mathematically supported by underlying volume flow.
</details>

#### 🧠 C. Machine Learning Layer (4 Models)
<details>
<summary><b>Click to expand Machine Learning Models</b></summary>
8.  **XGBoost Classifier:** Trained on historical OHLCV data using a walk-forward cross-validation window. Emits probabilities for Up (>2% in 5 days), Down (<-2% in 5 days), and Flat.
9.  **LightGBM Classifier:** Highly optimized, gradient-boosted decision tree layer natively handling complex engineered features like microstructure shadows.
10. **Lightweight Sequence Model:** A temporal sequence classifier designed to mimic LSTM networks, capturing cyclical sine-wave patterns in price action.
11. **Short-Term Multilayer Perceptron (MLP):** A deep neural network optimized to detect near-term order imbalances for 1-to-3 day thrusts.
</details>

#### 🏦 D. Microstructure & Flow (4 Models)
<details>
<summary><b>Click to expand Microstructure Models</b></summary>
12. **Smart Money / VPOC:** Scans intraday tape for high-density institutional accumulation (Demand Blocks) at the Volume Point of Control.
13. **StatArb Pairs Trading (Z-Score):** The `stat_arb.py` engine monitors highly cointegrated sector pairs (e.g., TCS vs INFY). Using verified rolling unit root testing, it triggers mean-reversion signals when the spread ratio deviates by more than $\pm2$ standard deviations from the historical mean.
14. **Institutional Flow (FII/DII):** Tracks net daily capital injection/extraction by Foreign and Domestic Institutional Investors into the Indian cash market.
15. **Options Put-Call Ratio (PCR):** Analyzes open interest across the derivatives chain to detect contrarian retail sentiment extremes.
</details>

---

### 2. Walk-Forward Optimization (WFO) Backtesting Logic

Agent Alpha’s Machine Learning classifiers were explicitly engineered to prevent "curve-fitting" and overfitting, utilizing a strict **Walk-Forward Optimization** protocol.
*   **The Problem with Static Data:** Traditional algorithms train on a random 80/20 split, failing to account for evolving market regimes.
*   **The WFO Solution:** Agent Alpha models are trained sequentially. A model is trained on the 2018-2022 window, then tested strictly on unseen 2023 data. The engine then rolls forward, re-training on 2019-2023, and testing on 2024. 

---

### 3. Risk Heatmap & Sector Correlation Matrix

Capital preservation relies heavily on preventing sector overexposure. Agent Alpha continuously calculates a dynamic **Pearson Correlation Matrix** across the active portfolio. 
*   **The Overexposure Veto:** If the system attempts to buy 5 different highly correlated IT stocks, the Correlation Matrix flags the beta-cluster.
*   **Dynamic Trimming:** The system will execute the highest-conviction signal in the cluster and automatically veto the redundant, correlated trades.

---

### 4. The "Self-Healing" Data Pipeline & Test Suite

External APIs (`yfinance`, FRED) are inherently unstable. Agent Alpha is built with a resilient pipeline heavily scrutinized by our automated testing suite:
*   **Exponential Backoff Retries:** Managed by `stock_fetcher.py`. If a server drops the connection, the cron engine automatically halts, waits, and retries the fetch.
*   **Database Fallbacks:** Validated by `test_db.py`. If an API goes dark, the engine falls back to historical records to prevent the ML ensemble from receiving NULL vectors.
*   **Z-Score Validations:** `test_zscore.py` routinely verifies the standard deviation math for statistical arbitrage pairs.

---

### 5. The Paper Trading Arena (The 10L Crucible)

The **Paper Trading Arena** is where models prove their worth. It operates with a strict **₹10 Lakh (`₹1,000,000`) Base Capital**.

*   **Cloud-Native Serverless Ledger:** All simulated trades, slippage calculations, open P&L, and margin utilizations are instantly logged and retrieved via our remote **Neon PostgreSQL** server, preventing localized file lock issues during heavy cron executions.
*   **Dynamic Margin Calculation:** Ensures that the 10L baseline is protected, utilizing Kelly Criterion to size bets appropriately without blowing up the account.
*   **Weekend Staleness Architecture:** Upgraded to natively handle 96-hour data staleness thresholds to gracefully maneuver over weekends without triggering false "stale data" vetos.

---

### 6. The 12-Rule Hard Veto Firewall

Before a signal generated by the Ensemble hits the 10L Arena, it is subjected to a **Zero-Trust Veto**:

<div align="center">
  <img src=".github/assets/diagrams/veto.png" alt="12-Rule Hard Veto Firewall" width="100%" style="border-radius: 12px; box-shadow: 0 4px 30px rgba(255,0,60,0.15);" />
</div>

---

## 🚨 Crisis Regime Strategy Execution

During major market drawdowns, Agent Alpha dynamically switches into the **Crisis Regime**. This protects capital using a Safe Haven strategy while strategically accumulating the broader market at a discount. Validated completely via `test_crisis.py`.

<div align="center">
  <img src=".github/assets/diagrams/crisis.png" alt="Crisis Regime Strategy Execution" width="100%" style="border-radius: 12px; box-shadow: 0 4px 30px rgba(0,255,136,0.15);" />
</div>

### Execution Logic

The conceptual diagram above translates to the following execution logic in our autonomous engine:

```python
# 🚨 CRISIS REGIME ACTIVATED
if market_regime == "CRISIS":
    
    # 🟡 Safe Haven: GOLD (5% allocation)
    if not portfolio.holds_asset("GOLDBEES"):
        execute_buy(symbol="GOLDBEES", allocation_pct=0.05)
        log_to_db_and_telegram("GOLDBEES: Safe haven activated")
        
    # 🔵 Value Accumulation: NIFTY 50 (5% allocation)
    if not portfolio.holds_asset("NIFTYBEES"):
        execute_buy(symbol="NIFTYBEES", allocation_pct=0.05)
        log_to_db_and_telegram("NIFTYBEES: Market accumulation activated")
```

---

## 🧮 Mathematical Models & Algorithmic Foundations

Agent Alpha relies on rigorous mathematical foundations for regime classification, volatility scaling, and position sizing.

### 1. Hidden Markov Model (HMM) Regime Classification
We model the market environment as a Hidden Markov Process to prevent lagging execution and whipsaws. The market state $\mathbf{X}_t$ is classified into one of 4 hidden states using a Gaussian HMM based on the observation vector:

$$ \mathbf{X}_t = \{ R_t, \sigma_{20}, \text{VIX}_t, \text{Breadth}_t, \Delta_{\text{EMA200}} \} $$

### 2. Average True Range (ATR) Volatility Sizing
Position size is dynamically adjusted so that the stop-loss distance equates to a maximum risk limit of $2\%$ of overall portfolio equity ($E$):

$$ \text{True Range (TR)} = \max(H - L, |H - C_{prev}|, |L - C_{prev}|) $$
$$ \text{ATR}_{14} = \frac{13 \times \text{ATR}_{prev} + \text{TR}}{14} $$
$$ \text{Stop Loss Distance} = 2 \times \text{ATR}_{14} $$
$$ \text{Position Value} = \frac{E \times 0.02}{\text{Stop Loss Distance} / \text{Price}} $$

### 3. Kelly Criterion Position Scaling
To prevent over-leveraging and drawdowns, raw Kelly fractions ($K_{\text{raw}}$) are computed based on historical win rates ($W$) and profit factors ($R$):

$$ K_{\text{raw}} = W - \frac{1 - W}{R} $$

This fraction is scaled dynamically by the regime modifier ($M_{\text{regime}}$) and the global pre-market bias score ($B_{\text{global}}$):

$$ K_{\text{final}} = K_{\text{raw}} \times M_{\text{regime}} \times (1 + B_{\text{global}}) $$

---

## ⚙️ System Requirements & Software Dependencies

### Hardware Requirements (Sentinel Node)
*   **CPU:** 8-Core Processor (Apple Silicon M1/M2/M3, Intel Core i7, or AMD Ryzen 7)
*   **RAM:** 16GB Minimum (32GB+ Highly Recommended for LLaMA 3.3 70B execution in memory)
*   **Storage:** 50GB NVMe SSD (Required for historical OHLCV parquet caching and Docker volumes)
*   **Network:** Uninterrupted high-speed broadband (for zero-latency API streaming)

### Software Dependencies
*   **Docker & Docker Compose:** Containerization and orchestrating the backend/cron stack.
*   **Python 3.10+:** The core runtime for the quantitative engine.
*   **Ollama:** Must be installed locally or accessible via IP to serve the `llama3.3:70b-versatile` model.
*   **Neon Serverless PostgreSQL:** For stateless ledger storage (`backend/database.py`).
*   **Core Python Libraries:** `fastapi`, `xgboost`, `lightgbm`, `pandas-ta`, `statsmodels`, `yfinance`.

---

## 🐳 Dockerization & Cloud Deployment Topology

Agent Alpha relies on a pristine, containerized deployment matrix to guarantee environment parity between the development Node and the Sentinel execution Node.

### Architecture Highlights:
*   **`docker-compose.yml` orchestration:** The backend FastAPI server, the cron scheduler, and the Python execution environments are wrapped into lightweight Docker containers with appropriately routed network ports (avoiding native Windows port clashing).
*   **Stateless Compute:** All persistent state is pushed to **Neon PostgreSQL**. If a Docker container goes down, it can be instantaneously rebuilt without losing a single cent of paper trading data.
*   **Deployment CI/CD (`deploy_to_dell.sh`):** A bash script specifically engineered to bypass Windows environment bugs by gracefully executing git pulls and docker container restarts on the remote Sentinel.

### Local Ignition Commands
```bash
git clone https://github.com/SaiSiddharthBS/MarketAnalyser.git
cd MarketAnalyser

# Create Environment File
cat <<EOT >> .env
DATABASE_URL=postgresql://user:pass@ep-host.neon.tech/neondb?sslmode=require
TELEGRAM_BOT_TOKEN=your_telegram_token
TELEGRAM_CHAT_ID=your_chat_id
GEMINI_API_KEY=your_gemini_api_key
EOT

# Build and deploy via Docker
docker-compose up --build -d
```

<br>
---

## 📸 System Gallery & Dashboards

**1. Agent Alpha Main Terminal Dashboard**
*Live streaming market analysis and overall portfolio standing within the Obsidian UI.*
<img src="Screenshots/1.png" width="100%" style="border-radius: 8px; margin-bottom: 20px;">

**2. Execution Ledger & Position Sizing**
*Real-time breakdown of capital allocation and Kelly Criterion margin utilization.*
<img src="Screenshots/1.2.png" width="100%" style="border-radius: 8px; margin-bottom: 20px;">

**3. Hidden Markov Model Regime Classifier**
*Dynamic 4-state probability matrix assessing overarching market risk.*
<img src="Screenshots/2.png" width="100%" style="border-radius: 8px; margin-bottom: 20px;">

**4. 15-Model Ensemble Voting Interface**
*Granular breakdown of technical, momentum, and machine learning predictions.*
<img src="Screenshots/3.png" width="100%" style="border-radius: 8px; margin-bottom: 20px;">

**5. Machine Learning Predictors**
*Out-of-sample directional probabilities and feature importance from XGBoost & LightGBM.*
<img src="Screenshots/4.png" width="100%" style="border-radius: 8px; margin-bottom: 20px;">

**6. Statistical Arbitrage Cointegration Heatmap**
*Z-score deviation tracking for advanced mean-reversion pairs trading.*
<img src="Screenshots/5.png" width="100%" style="border-radius: 8px; margin-bottom: 20px;">

**7. Microstructure & Smart Money Flow**
*Intraday VPOC migration and institutional volume orderblock analysis.*
<img src="Screenshots/6.png" width="100%" style="border-radius: 8px; margin-bottom: 20px;">

**8. Options Open Interest (PCR) Dashboard**
*Contrarian retail sentiment tracker derived from the live derivatives chain.*
<img src="Screenshots/6.2.png" width="100%" style="border-radius: 8px; margin-bottom: 20px;">

**9. The 12-Rule Veto Firewall Activity Log**
*Real-time risk mitigation blocking trades during severe market anomalies.*
<img src="Screenshots/7.png" width="100%" style="border-radius: 8px; margin-bottom: 20px;">

**10. Correlation Matrix Safeguard**
*Ensuring strict adherence to sector beta limits to prevent algorithmic overexposure.*
<img src="Screenshots/7.2.png" width="100%" style="border-radius: 8px; margin-bottom: 20px;">

**11. Crisis Regime Action Protocol**
*Active Safe Haven (Gold) and Index accumulation defensive parameters.*
<img src="Screenshots/7.3.png" width="100%" style="border-radius: 8px; margin-bottom: 20px;">

**12. Database & Ledger Verification**
*Remote Neon PostgreSQL status logs for the Paper Trading execution environment.*
<img src="Screenshots/8.png" width="100%" style="border-radius: 8px; margin-bottom: 20px;">

**13. LLM Catalyst & News Sentiment Parser**
*LLaMA 3.3 70B parsing live financial streams via local Ollama deployment.*
<img src="Screenshots/8.2.png" width="100%" style="border-radius: 8px; margin-bottom: 20px;">

**14. Sentinel Docker Node Health**
*Live metrics from the always-on execution server running the cron daemons.*
<img src="Screenshots/9.png" width="100%" style="border-radius: 8px; margin-bottom: 20px;">

**15. Telegram Sub-System Alert Channel**
*Instant push notifications for every trade execution, signal drift, and system veto.*
<img src="Screenshots/10.png" width="100%" style="border-radius: 8px; margin-bottom: 20px;">

<br>
<div align="center">
  <i>"The future of finance is not predicted. It is computed."</i><br/>
  <b>— Agent Alpha</b>
</div>
