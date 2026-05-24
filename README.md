<div align="center">
  <img src=".github/assets/hero_banner.png" alt="Agent Alpha Hero Banner" width="100%">
  
  <h1><b>🦅 AGENT ALPHA v3.0</b></h1>
  <p><b>The Quantitative Multi-Ensemble & Hidden Markov Model Autonomous Trading Infrastructure</b></p>
  
  [![Production Live](https://img.shields.io/badge/Status-Production_Live-00ffcc?style=for-the-badge&logo=statuspage&logoColor=black)]()
  [![Python](https://img.shields.io/badge/Python-3.10+-7f00ff?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
  [![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
  [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org/)
  [![LightGBM](https://img.shields.io/badge/LightGBM-ff007f?style=for-the-badge&logo=cpu&logoColor=white)](https://github.com/microsoft/LightGBM)
  [![XGBoost](https://img.shields.io/badge/XGBoost-ffcc00?style=for-the-badge&logo=nvidia&logoColor=black)](https://xgboost.ai/)
</div>

---

## 💻 Obsidian Glass UI Mockup

Below is a visual representation of the **Obsidian Glass UI Dashboard** presenting real-time system equity metrics, position distributions, HMM regime transitions, and quantitative indicators in production:

<div align="center">
  <img src=".github/assets/dashboard_mockup.png" alt="Obsidian Glass UI Dashboard Mockup" width="90%" style="border-radius: 12px; border: 2px solid #00ffcc; box-shadow: 0 0 20px rgba(0,255,204,0.3);">
</div>

---

## 🗺️ High-Tech System Architecture Map

The visual blueprint below details the synchronous and asynchronous execution flows across the **6-Layer Quantitative Pipeline**:

```mermaid
graph TD
    %% Custom Styling Defs
    classDef layer1 fill:#ff007f,stroke:#ff007f,stroke-width:2px,color:#fff;
    classDef layer2 fill:#7f00ff,stroke:#7f00ff,stroke-width:2px,color:#fff;
    classDef layer3 fill:#00ffcc,stroke:#00ffcc,stroke-width:2px,color:#000;
    classDef layer4 fill:#ffcc00,stroke:#ffcc00,stroke-width:2px,color:#000;
    classDef database fill:#1e1e2e,stroke:#cdd6f4,stroke-width:1px,color:#cdd6f4;
    classDef external fill:#11111b,stroke:#a6e3a1,stroke-width:1px,color:#a6e3a1;

    %% Data flow nodes
    subgraph L1 ["Layer 1: Pre-Market & Data Validation"]
        PRE[Premarket Scraper]
        VAL[DataValidator]
        MAC[Macro Calendar Veto]
    end
    
    subgraph L2 ["Layer 2: 15-Model Ensemble Router"]
        ENS[Ensemble Voter Engine]
        VOT[Model Correlation Calculator]
    end
    
    subgraph L3 ["Layer 3: Hidden Markov Model (HMM)"]
        HMM[Gaussian HMM Classifier]
        REG[Regime Weight Adapter]
    end
    
    subgraph L4 ["Layer 4 & 5: Position & Execution"]
        VETO[12-Rule Veto Firewall]
        SIZE[Kelly / ATR Sizer]
        OPT[Portfolio Optimizer]
    end
    
    %% External API's
    YF([yfinance API]) -->|Raw OHLCV| VAL
    FRED([FRED API]) -->|Macro Series| PRE
    
    %% Internal flows
    VAL -->|Fresh & Checked Data| ENS
    PRE -->|Global Index Changes| HMM
    MAC -->|Event Blockers| VETO
    
    HMM -->|Dynamic Sizing Multiplier| SIZE
    ENS -->|Weighted Directives| VETO
    VETO -->|Cleared Setups| SIZE
    SIZE -->|Target Allocations| OPT
    
    %% Storage links
    OPT -->|Execute Open Positions| DB[(Neon Postgres Serverless)]
    DB <-->|Sync State| UI[Obsidian Glass UI]
    
    %% Assign Styles
    class PRE,VAL,MAC layer1;
    class ENS,VOT layer2;
    class HMM,REG layer3;
    class VETO,SIZE,OPT layer4;
    class DB,UI database;
    class YF,FRED external;
```

---

## 🧠 Comprehensive Codebase Inventory (43 Modules Deployed)

Every quant module deployed between **April 30th and May 24th, 2026** is documented below with its exact function, file path, and algebraic formulas:

```
                          AGENT ALPHA CORE DIRECTORY
                                      │
         ┌────────────────────────────┼────────────────────────────┐
         ▼                            ▼                            ▼
     [Analysis]                     [Data]                       [Bot]
 (43 Core Quant Engines)      (Validation & Flow)        (Alerts & Scheduling)
```

---

### 📂 Analysis Layer (`/backend/analysis/`)

#### 1. `ensemble.py` (The Central Voting Router)
*   **Role:** Integrates signals from 15 models. Resolves conflicting directional vectors.
*   **Formula:** Blends 15 dynamic votes ($V_i$) using regime-dependent weights ($W_i$) to output the raw confidence score ($C_{\text{raw}}$):
    $$C_{\text{raw}} = \sum_{i=1}^{15} V_i \times W_i(Regime) + \text{Sector Rotation Boost} \pm \text{RVOL Penalty}$$
*   **Interfacing:** Accepts calculated indicators from `technical.py` and predictions from `ml_engine.py`, then pipes targets to `veto_engine.py`.

#### 2. `regime.py` (Gaussian Hidden Markov Classifier)
*   **Role:** Fits a 4-state Gaussian Hidden Markov Model (HMM) on historical indexes (Nifty 50) and macro volatility.
*   **Formula:** Solves the transition matrix $P$ to determine the most likely hidden state sequence:
    $$P(S_t = j \mid S_{t-1} = i) = p_{ij}$$
*   **Interfacing:** Downloads Nifty 50 and India VIX data via `stock_fetcher.py`, updates weights, and outputs modifiers to `ensemble.py`.

#### 3. `backtest_engine.py` (Walk-Forward Simulator)
*   **Role:** Performs strict walk-forward backtests. Accounts for execution lags, slippage, and transactional costs.
*   **Formula:** Simulates standard brokerage, Securities Transaction Tax (STT), and capital impact costs:
    $$\text{Buy Price}_{\text{effective}} = \text{Open Price} \times (1 + \text{Slippage Pct}) + \text{STT} + \text{Brokerage}$$
*   **Interfacing:** Operates over processed historical outputs generated from the ensemble vectors.

#### 4. `veto_engine.py` (Rule Firewall)
*   **Role:** Enforces 12 strict safety rules. Any single rule violation instantly triggers a `STAND ASIDE` override.
*   **Interfacing:** Reads stock-specific corporate metadata, market regime alerts, and portfolio drawdown states.

#### 5. `ml_engine.py` (LightGBM/XGBoost Tabular Pipeline)
*   **Role:** Trains LightGBM and XGBoost classifiers. Emits out-of-sample directional probabilities.
*   **Validation:** Employs `TimeSeriesSplit` with a 5-day gap to prevent temporal look-ahead leakage.
*   **Interfacing:** Consumes engineered tabular features from `feature_engineer.py`.

#### 6. `transformer_engine.py` (lightweight Sequence Model)
*   **Role:** Captures temporal order patterns in price movements (e.g. consolidation -> breakout).
*   **Architecture:** Implements sequence prediction using HistGradientBoosting over 60-day lagged inputs.
*   **Interfacing:** Connects to `ensemble.py` as Model 10 in the voting array.

#### 7. `lstm_engine.py` (MLP Classifier Timing Layer)
*   **Role:** Predicts short-term price direction (1-3 day horizon). Serves as a fast timing layer.
*   **Interfacing:** Fits a normalized MLP classifier over short-term returns and volatility velocity.

#### 8. `overnight_intel.py` (Global Macro Scanner)
*   **Role:** Runs daily at 6:00 AM IST. Analyzes US markets, Asian futures, commodities, bonds, and crypto risk sentiment.
*   **Formula:** Computes a composite global score ($S_{\text{global}}$):
    $$S_{\text{global}} = \sum_{k} \Delta \text{Asset}_k \times \text{Weight}_k$$
*   **Interfacing:** Transmits pre-market briefings to Telegram and adjusts baseline trading thresholds.

#### 9. `sector_rotation.py` (Sector Rotation command Center)
*   **Role:** Dynamically calculates relative strength across all major NSE indices vs the Nifty 50 benchmark.
*   **Formula:** Integrates weighted performance parameters:
    $$\text{Score}_{\text{composite}} = 3 \times (\text{RS vs Nifty}) + 0.1 \times (\text{Breadth} - 50) + 5 \times (\text{RVOL} - 1)$$
*   **Interfacing:** Applies score boosts or penalties to stocks in the ensemble.

#### 10. `smart_money.py` (Volume Profile & VPOC Engine)
*   **Role:** Extracts Volume Point of Control (VPOC) and identifies institutional demand/supply order blocks using intraday data.
*   **Interfacing:** Feeds order imbalance calculations into `ensemble.py`.

#### 11. `stat_arb.py` (Pairs Trading Cointegration Engine)
*   **Role:** Evaluates statistical spreads on cointegrated asset pairs in Nifty 50.
*   **Formula:** Calculates the rolling z-score of log spreads:
    $$\text{Z-Score} = \frac{\text{Spread}_t - \mu_{\text{Spread}}}{\sigma_{\text{Spread}}}$$
*   **Interfacing:** Emits buy/sell pairs signals to the optimizer.

#### 12. `feature_engineer.py` (Engineered Feature Generator)
*   **Role:** Computes 50+ quantitative features (e.g., ADX, MACD, Bollinger Bands, Williams %R, shadow proxies) from raw prices.
*   **Interfacing:** Inputs matrices to `ml_engine.py` and `lstm_engine.py`.

#### 13. `position_sizing.py` (Kelly/ATR Sizing Optimizer)
*   **Role:** Calculates position allocations using a strict maximum portfolio risk limit of 2% per trade.
*   **Formula:** Calculates the stop-loss distance using Average True Range:
    $$\text{SL Distance} = 2 \times \text{ATR}_{14}$$
    $$\text{Sizing Fraction} = K_{\text{raw}} \times M_{\text{regime}}$$
*   **Interfacing:** Restricts execution sizes for candidates going to `portfolio_optimizer.py`.

#### 14. `portfolio_optimizer.py` (Correlation Optimizer)
*   **Role:** Prevents over-concentration in highly correlated stocks or identical sectors.
*   **Interfacing:** Calculates a covariance matrix and prunes redundant candidates.

#### 15. `timeframe_classifier.py` (Dynamic Holding Period Classifier)
*   **Role:** Classifies setup swing holding periods (Intraday, Short-Term, Swing, Positional, Long-Term).
*   **Formula:** Evaluates volatility (ATR%) and trend alignment.
*   **Interfacing:** Sets target expiration dates for open paper positions.

#### 16. `technical.py` (Fundamental Indicator Core)
*   **Role:** Computes core technical indicators and calculates a raw technical score.
*   **Interfacing:** Standardizes basic metrics for the first ensemble layer.

#### 17. `patterns.py` (Chart Pattern Recogniser)
*   **Role:** Detects structural double tops, double bottoms, morning stars, and engulfing candles.
*   **Interfacing:** Adjusts technical confidence parameters inside `ensemble.py`.

#### 18. `accuracy.py` (Accuracy Auditor)
*   **Role:** Compares predicted targets against real market outcomes 5 days post-signal.
*   **Interfacing:** Resolves active rows in the database, updating the self-learning loop.

#### 19. `advisor.py` (Gemini Advisory Gateway)
*   **Role:** Leverages Gemini to generate structured morning briefings for Sai's portfolio.
*   **Interfacing:** Fetches active database positions and formats markdown reports.

#### 20. `montecarlo.py` (Simulated Out-of-Sample Simulator)
*   **Role:** Generates 5,000 randomized walk-forward paths to evaluate maximum drawdown probabilities.
*   **Interfacing:** Provides risk metrics for the advisory reports.

#### 21. `fno_signals.py` (Derivatives Trend Classifier)
*   **Role:** Calculates Implied Volatility (IV) percentiles and Open Interest (OI) buildup changes.
*   **Interfacing:** Provides veto triggers for option danger flags.

#### 22. `walk_forward.py` (Cross-Validation Helper)
*   **Role:** Manages rolling train-test indexing matrices.
*   **Interfacing:** Feeds clean indices to `ml_engine.py` during walk-forward training.

#### 23. `veto_log.py` / `error_analyzer.py` / `trade_explainer.py`
*   **Role:** Logs failed setups, analyzes prediction error classifications, and generates explanations for portfolio transactions.

---

### 📂 Data & System Layer (`/backend/data/` & `/backend/`)

#### 24. `database.py` (Dual PostgreSQL-SQLite Pooler)
*   **Role:** Connects to Postgres on cloud (using `psycopg2` Threaded Connection Pooling) and SQLite locally.
*   **Interfacing:** Automates query translation, maintains daily schema updates, and handles migrations.

#### 25. `data_validator.py` (Immune System Check)
*   **Role:** Enforces high data quality. Drops rows with missing metrics or data older than 96 hours.
*   **Interfacing:** Protects `stock_fetcher.py` and ML inputs from bad Yahoo Finance feeds.

#### 26. `stock_fetcher.py` (OHLCV Scraper)
*   **Role:** Fetches historical and intraday market prices with standard fallbacks.
*   **Interfacing:** Caches prices inside `database.py` before passing them to validation.

#### 27. `scheduler.py` (System Scheduler Daemon)
*   **Role:** Decoupled process manager. Coordinates execution times for the daily jobs.
*   **Schedule:** 6:00 AM IST (Global scan) and 3:45 PM IST (Closing paper engine execution).

---

### 📂 Alert & Bot Layer (`/backend/bot/` & `/backend/services/`)

#### 28. `daily_job.py` (Master Pipeline Orchestrator)
*   **Role:** Runs the quant pipeline step-by-step. Coordinates indicators, regimes, vetoes, and sends Telegram updates.

#### 29. `telegram_bot.py` (Command Interface Bot)
*   **Role:** Sets up interactive Telegram command handlers (`/analyze`, `/market`, `/screener`, `/portfolio`, `/paper`).

---

## 🎨 Colorful Mindmap of System Directory

The mindmap below outlines the core quant packages, styled with bright cyber-color tags:

```mermaid
mindmap
  root((Agent Alpha v3.0))
    ::icon(fa fa-shield)
    ::style(fill:#ff007f,stroke:#ff007f,stroke-width:3px,color:#fff)
    Analysis
      ::style(fill:#7f00ff,stroke:#7f00ff,stroke-width:2px,color:#fff)
      Models
        ::style(fill:#00ffcc,stroke:#00ffcc,stroke-width:1px,color:#000)
        ensemble.py (weighted votes)
        ml_engine.py (lightgbm/xgb)
        transformer_engine.py (sequence)
        lstm_engine.py (mlp timing)
        stat_arb.py (cointegration pairs)
      Regimes
        ::style(fill:#ffcc00,stroke:#ffcc00,stroke-width:1px,color:#000)
        regime.py (hmm 4-states)
        overnight_intel.py (global score)
        sector_rotation.py (index momentum)
      Validation
        ::style(fill:#00ff00,stroke:#00ff00,stroke-width:1px,color:#000)
        veto_engine.py (12-rule firewall)
        backtest_engine.py (walk-forward costs)
        accuracy.py (outcome grading)
    Data Layer
      ::style(fill:#7f00ff,stroke:#7f00ff,stroke-width:2px,color:#fff)
      database.py (neon connection pool)
      data_validator.py (96h staleness safety)
      stock_fetcher.py (yahoo finance)
    Interface
      ::style(fill:#7f00ff,stroke:#7f00ff,stroke-width:2px,color:#fff)
      daily_job.py (master cron script)
      telegram_bot.py (interactive bot commands)
      main.py (fastapi routes gateway)
```

---

## 🚀 Deployed System Lifecycles & Timelines

### 1. Pre-Market Intelligence (Daily 6:00 AM - 9:00 AM IST)
*   **Step 1:** Cron scheduler triggers `overnight_intel.py`.
*   **Step 2:** System downloads indices, commodities, currencies, and bonds from Yahoo Finance.
*   **Step 3:** Computes global risk sentiment score and sends a pre-market overview to Telegram.
*   **Step 4:** Adjusts the model's setup conviction thresholds for the day (e.g. tightening thresholds if global markets are down).

### 2. Paper Trading Arena Run (Daily 3:45 PM IST)
*   **Step 1:** Cron triggers the screener via `daily_job.py`.
*   **Step 2:** Downloads closing price data, runs feature engineering, and calculates HMM states.
*   **Step 3:** Gathers votes from all 15 models.
*   **Step 4:** Runs approved setups through the Veto Firewall.
*   **Step 5:** Allocates sizes using the 2% ATR Risk model and executes positions in Postgres.
*   **Step 6:** Triggers Telegram updates showing execution logs and equity curves.

---

## ⚡ Deployment & Local Setup

Agent Alpha is containerized and ready for immediate deployment.

### 1. Install & Configure
```bash
git clone https://github.com/SaiSiddharthBS/MarketAnalyser.git
cd MarketAnalyser
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment variables (.env)
Create a `.env` file in the root directory:
```env
DATABASE_URL=postgresql://user:pass@ep-host.neon.tech/neondb?sslmode=require
TELEGRAM_BOT_TOKEN=your_telegram_token
TELEGRAM_CHAT_ID=your_chat_id
GEMINI_API_KEY=your_gemini_api_key
```

### 3. Run the Execution Gateway
```bash
# Start FastAPI backend (serves Obsidian Glass UI on http://localhost:8000)
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### 4. Run the Background Scheduler Daemon
```bash
# Launches the background execution clock for daily jobs
python backend/scheduler.py
```

---

<div align="center">
  <i>"The future of finance is not predicted. It is computed."</i><br/>
  <b>— Agent Alpha v3.0 Core</b>
</div>
