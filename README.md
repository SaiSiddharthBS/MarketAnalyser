<div align="center">
  <img src="Agent%20Alpha%20Logo%20v2.png" alt="Agent Alpha Logo" width="150" />
  
  <h1><b style="color: #00FF88;">AGENT ALPHA v3.0</b> | <i>The Apex of Algorithmic Trading</i></h1>
  <p><b>Institutional-Grade Algorithmic Trading Core & Quantitative AI Ensemble Engine</b></p>

  <img src=".github/assets/agent_alpha_terminal_ui.png" alt="Agent Alpha Terminal UI" width="100%" style="border-radius: 12px; box-shadow: 0 4px 30px rgba(0,255,136,0.2); margin-top: 20px;" />

  <br><br>

  [![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
  [![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
  [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org/)
  [![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
  [![XGBoost](https://img.shields.io/badge/XGBoost-FF9800?style=for-the-badge&logo=nvidia&logoColor=white)](https://xgboost.ai/)
  [![Status](https://img.shields.io/badge/Status-Production_Live-success?style=for-the-badge)]()
</div>

<hr style="border: 1px solid rgba(255,255,255,0.1);">

## 📖 Executive Overview

**Agent Alpha** is not just an indicator; it is a **fully autonomous, highly scalable, and production-ready quantitative intelligence system** designed to outmaneuver the Indian Stock Market (Nifty 50 universe). Combining the bleeding edge of machine learning, statistical arbitrage, and a deeply optimized paper trading arena, Agent Alpha represents a CEO-level deployment of quantitative logic.

We threw out the idea of simple rule-based trading. Instead, we architected a **15-Model Machine Learning Ensemble** spanning tabular classifiers (like **XGBoost** and **LightGBM**), sequence-based neural networks, statistical arbitrage, and macro microstructure analysis.

With **Zero-Trust Capital Preservation Architecture**, every signal must survive a **4-State Hidden Markov Model (HMM) Regime Classifier**, navigate a ruthless **12-Rule Hard Veto Firewall**, and calculate its weight via **ATR & Kelly Criterion Position Sizing**. 

---

## ⏱️ Multi-Horizon Trading Expertise

Agent Alpha is not confined to a single timeframe. The engine dynamically scales its analysis across three distinct temporal horizons, ensuring alpha extraction regardless of market speed.

1. **Intraday Microstructure (High-Frequency Context):**
   Scans the first 45 minutes of the trading session for Smart Money block orders and Volume Point of Control (VPOC) migrations to gauge institutional sentiment before executing swing trades.
2. **Short-Term Swing & Momentum (The Core Engine):**
   Optimized for a 3-to-15 day holding period. Leverages the LightGBM classifiers and ROC/MACD momentum matrices to ride the primary thrust of the prevailing market wave, minimizing overnight gap risk while capturing maximum velocity.
3. **Long-Term Macro (Regime Filtering):**
   Monitors the 200-day EMA, FII/DII institutional flow, and India VIX to dictate the overarching **Hidden Markov Model (HMM) State**. Prevents the system from buying long-term secular downtrends or systemic crises.

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
      Sector Correlation Heatmap
      ATR & Kelly Position Sizing
    Data & Infrastructure
      yfinance & FRED APIs
      Neon PostgreSQL
      Docker Containerization
      Decoupled Cron Daemons
    Execution & Reporting
      Paper Trading Arena
      ₹10L Starting Capital
      Telegram Bot Alerts
      Obsidian Glass UI
```

---

## 🏗️ Hardware Architecture: The Dual-Node Setup

Agent Alpha operates on a resilient, distributed physical architecture split across two synchronized machines. This ensures absolute separation of heavy quantitative compute processes and the executive visualization/monitoring dashboard.

```mermaid
graph TB
    subgraph "Node 1: Primary Compute & Dev Station (MacBook Pro)"
        direction TB
        Docker["Docker Engine"]
        FastAPI["FastAPI Uvicorn Backend"]
        Cron["Background Scheduler Daemon"]
        Quant["15-Model Quant Engine"]
        Dev["Codebase & Strategy Backtesting"]
        
        Docker --> FastAPI
        Docker --> Cron
        Cron --> Quant
    end

    subgraph "Node 2: The Sentinel UI Node (Secondary Laptop)"
        UI["Obsidian Glass UI (Local PWA)"]
        UI_Browser["Google Chrome / Safari<br/>(60 FPS Chart Rendering)"]
    end

    subgraph "Cloud Infrastructure"
        DB[("Neon PostgreSQL<br/>(Serverless Cluster)")]
        TG["Telegram API"]
        Data["yfinance / FRED APIs"]
    end

    UI_Browser -.->|Local Network REST / WebSockets| FastAPI
    Quant -->|Write P&L / Read Ledger| DB
    Quant -->|Fetch OHLCV / Auto-Heal Cache| Data
    Cron -->|Dispatch Alerts| TG
```

**Node 1 (Primary Station - MacBook Pro):** The computational powerhouse. This machine runs the `docker-compose` stack housing the FastAPI backend, the automated cron daemons, the machine learning models, and the data-fetching architecture. It is fully responsible for all algorithmic heavy-lifting and trade generation.
**Node 2 (Sentinel Display Node - Secondary Laptop):** A dedicated, always-on executive monitor. It runs the Obsidian Glass UI web app locally, fetching JSON payloads and rendering the 60FPS TradingView charts via WebSockets/REST. It remains untouched by backend latency, serving solely as the CEO's dashboard.

---

## 🧠 Core System Modules & Deep Dives

### 1. The 15-Model Quantitative Ensemble Engine

At the heart of Agent Alpha lies a weighted voting ensemble that outputs a continuous directional bias. 

#### 🚀 Machine Learning Classifiers: XGBoost & LightGBM
*   **XGBoost Classifier:** Emits probabilities for 3 classes: Up (>2% in 5 days), Down (<-2% in 5 days), and Flat.
*   **LightGBM Classifier:** Highly optimized, gradient-boosted decision tree layer natively handling complex engineered features (e.g. microstructure shadows, volume profiles).
*   **Lightweight Sequence Model & Short-Term MLP:** Temporal classifiers mimicking LSTM networks to capture cyclical wave patterns and order imbalances.

#### 📊 Microstructure & Statistical Arbitrage
*   **StatArb Pairs Trading:** Monitors highly cointegrated sector pairs.
*   **Smart Money / VPOC:** Scans intraday data for high-density institutional accumulation block trades.

---

### 2. Walk-Forward Optimization (WFO) Backtesting Logic

Agent Alpha’s Machine Learning classifiers were explicitly engineered to prevent "curve-fitting" and overfitting, utilizing a strict **Walk-Forward Optimization** protocol rather than a standard static backtest.
*   **The Problem with Static Data:** Traditional algorithms train on a random 80/20 split, failing to account for evolving market regimes.
*   **The WFO Solution:** Agent Alpha models are trained sequentially. A model is trained on the 2018-2022 window, then tested strictly on unseen 2023 data. The engine then rolls forward, re-training on 2019-2023, and testing on 2024. This simulates genuine "out-of-sample" predictive logic, ensuring the XGBoost and LightGBM models understand shifting macro-dynamics before they are deployed to the live Arena.

---

### 3. Risk Heatmap & Sector Correlation Matrix

Capital preservation relies heavily on preventing sector overexposure. 
Agent Alpha continuously calculates a dynamic **Pearson Correlation Matrix** across the active portfolio. 
*   **The Overexposure Veto:** If the system attempts to buy 5 different highly correlated IT stocks (e.g., TCS, INFY, HCLTECH), the Correlation Matrix flags the beta-cluster.
*   **Dynamic Trimming:** The system will execute the highest-conviction signal in the cluster and automatically veto the redundant, correlated trades. This forces capital to be deployed across orthogonal (uncorrelated) vectors, actively dampening portfolio variance and shielding the 10L capital pool from localized sector collapses.

---

### 4. The "Self-Healing" Data Pipeline

Data is the lifeblood of a quant engine. External APIs (`yfinance`, FRED) are inherently unstable, often suffering rate limits, timeouts, or corrupted OHLCV prints. Agent Alpha employs a **Self-Healing Data Pipeline**:
*   **Exponential Backoff Retries:** If the yfinance server drops the connection, the cron engine automatically halts, waits, and retries the fetch with an exponential backoff.
*   **SQLite Fallback Cache:** If an API goes completely dark, the engine falls back to the local SQLite database snapshot from the previous close, preventing the ML ensemble from executing on NULL vectors.
*   **Anomaly Detection:** Any sudden 20%+ unverified spike in a single 15-minute candle is quarantined by the data validator as a "Bad Tick" until cross-verified, preventing catastrophic execution errors.

---

### 5. The Paper Trading Arena (The 10L Crucible)

The **Paper Trading Arena** is where models prove their worth. Rigorously stress-tested, the Arena operates with a strict **₹10 Lakh (`₹1,000,000`) Base Capital**.

*   **Real-time Ledger:** Deducts margin, tracks open P&L, and accounts for brokerage and slippage. We rigidly reset the capital logic to 10L to preserve mathematical integrity and prevent long/short miscalculations.
*   **Dynamic Margin Calculation:** Ensures that the 10L baseline is protected, utilizing Kelly Criterion to size bets appropriately without blowing up the account.
*   **Weekend Staleness Architecture:** Upgraded to natively handle 96-hour data staleness thresholds to gracefully maneuver over weekends without triggering false "stale data" vetos.

---

### 6. The 12-Rule Hard Veto Firewall

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

## 🧮 Quantitative Mathematics & Formulas

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

## 🐳 Dockerization & Cloud Deployment Topology

Agent Alpha relies on a pristine, containerized deployment matrix to guarantee environment parity between the development Node and the Sentinel execution Node.

### Architecture Highlights:
*   **`docker-compose.yml` orchestration:** The backend FastAPI server, the cron scheduler, and the Python execution environments are wrapped into lightweight Docker containers.
*   **Stateless Compute:** All persistent state (Paper Arena Ledgers, Historical P&L) is pushed to **Neon Serverless PostgreSQL**. If a Docker container goes down, it can be instantaneously rebuilt without losing a single cent of paper trading data.
*   **Dependency Locking:** `requirements.txt` maps explicitly verified library versions to prevent `yfinance` or `xgboost` upstream breaks from crashing the engine.

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
<div align="center">
  <i>"The future of finance is not predicted. It is computed."</i><br/>
  <b>— Agent Alpha v3.0 Core</b>
</div>
