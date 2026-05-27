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
- [What's New in v4.0 (Spring 2026 Update)](#-whats-new-in-v40-spring-2026-update)
- [Enterprise Feature Suite](#-enterprise-feature-suite-ui-vs-autonomous-engine)
- [Multi-Horizon Trading Expertise](#-multi-horizon-trading-expertise)
- [Why Agent Alpha?](#-why-agent-alpha)
- [Architecture & Topology](#-hardware-architecture-the-dual-node-setup)
- [15-Model Ensemble & Deep Dives](#-core-system-modules--deep-dives)
- [The 12-Rule Hard Veto Firewall](#-the-12-rule-hard-veto-firewall)
- [Mathematical Foundations](#-mathematical-models--algorithmic-foundations)
- [Testing Suite & Resiliency](#-the-self-healing-data-pipeline--exhaustive-testing-suite)
- [Deployment Topology](#-dockerization--cloud-deployment-topology)
- [System Gallery & Dashboards](#-system-gallery--dashboards)

---

## 📖 Executive Overview

**Agent Alpha** is not just an indicator; it is a **fully autonomous, highly scalable, and production-ready quantitative intelligence system** designed to outmaneuver the Indian Stock Market (Nifty 50 universe). Combining the bleeding edge of machine learning, statistical arbitrage, and a deeply optimized paper trading arena, Agent Alpha represents a CEO-level deployment of quantitative logic.

Since day 1 (April 30th, 2026), we threw out the idea of simple rule-based trading. Instead, we architected a **15-Model Machine Learning Ensemble** spanning tabular classifiers (like **XGBoost** and **LightGBM**), sequence-based neural networks, statistical arbitrage, and macro microstructure analysis.

With our **Zero-Trust Capital Preservation Architecture**, every signal must survive a **4-State Hidden Markov Model (HMM) Regime Classifier**, navigate a ruthless **12-Rule Hard Veto Firewall**, and calculate its weight via **ATR & Kelly Criterion Position Sizing**. 

---

## 🚀 What's New in v4.0 (Spring 2026 Update)
*Agent Alpha v4.0 introduces the most significant systemic overhauls since inception. The focus shifted heavily from local scripting to cloud-native resilience, extreme UI refinement, and autonomous mathematical stress-testing.*

*   **The Database Deadlock Wars (Neon PostgreSQL Migration):** We completely ripped out local SQLite DB files (which were prone to severe Docker volume corruption and file locking) and integrated a fully cloud-native **Neon PostgreSQL** serverless instance (`backend/database.py`). To solve severe SQLAlchemy connection exhaustion during high-frequency paper trading, we engineered strict `pool_size=5` and `max_overflow=10` pooling logic, implemented recursion protection, and built explicit fail-safes like `kill_pg_locks.py` and `fix_locks.py` to make the remote ledger utterly bulletproof.
*   **Obsidian Glass UI & React Terminal:** Upgraded the entire frontend from a standard dark theme to the stunning "Obsidian Terminal" aesthetic. We deployed a fully interactive, React-based web terminal (`frontend/react_terminal`) allowing you to click through the Agent Alpha architecture. Features deep obsidian teal layers (`#051114`), glowing cyber-green borders (`#00FF88`), and fluid micro-animations.
*   **macOS Native Menubar Application:** Built a dedicated, native macOS utility (`backend/menubar_app.py`) allowing the CEO to start, stop, and monitor the live quantitative engine and P&L directly from the Mac's top status bar, entirely bypassing the browser.
*   **Programmatic Diagram Rendering Pipeline:** We explicitly abandoned GitHub's buggy markdown Mermaid renderer. Instead, we engineered a local Puppeteer + `mermaid-cli` pipeline that injects custom CSS to programmatically generate true 4K, glassmorphic, glowing PNGs of our architecture diagrams, perfectly preserving typography and layout.
*   **Sentinel Node Automation (`deploy_to_dell.sh`):** Implemented a flawless CI/CD bash script to instantly push deployments from the MacBook Pro to the Always-On Windows Sentinel node, effectively bypassing inherent Windows pathing and WSL Docker network clashing issues.

---

## 🔥 Enterprise Feature Suite: UI vs. Autonomous Engine

### 🧠 Autonomous Execution & AI
*   **Zero-Latency Signal Generation:** Engine processes OHLCV ticks, calculates 15 model vectors, and generates a unified bias in `<400ms`.
*   **LLM Catalyst Engine (Ollama + LLaMA 3.3 70B):** Natively ingests live news headlines and complex corporate SEC/NSE filings. Instead of relying on generic cloud APIs, it routes sentiment analysis and financial parsing through a highly-capable, locally-hosted **LLaMA 3.3 70B Versatile** model via **Ollama**, ensuring zero data leakage, unthrottled inference speed, and institutional-grade reasoning.
*   **Walk-Forward ML Optimization (WFO):** Models never curve-fit. They are trained sequentially on rolling windows to guarantee out-of-sample robustness.

### 🛡️ Institutional Risk Management
*   **Dynamic Kelly Criterion:** Position sizing isn't guessed. It is mathematically derived from the historical win-rate and profit factor of the active HMM regime.
*   **Dynamic Correlation Heatmap:** Actively calculates Pearson correlation across the portfolio to prevent localized sector beta-collapse.

### ⚡ The Command & Control Interfaces
*   **The Obsidian Glass Executive PWA:** A gorgeous, hardware-accelerated dashboard featuring 60FPS WebSockets for live execution LED pulses, real-time P&L tickers, and portfolio drawdown metrics streamed directly from the Python backend.
*   **Interactive Telegram Sub-System:** We moved far beyond basic push notifications. The `bot` directory houses a fully interactive, two-way Telegram command center. You receive live execution alerts, but you can also text `/status`, `/holdings`, and `/stop` to remotely monitor or kill the engine directly from your phone while on the move.

---

## ⏱️ Multi-Horizon Trading Expertise

Agent Alpha dynamically scales its analysis across three distinct temporal horizons, ensuring alpha extraction regardless of market speed.

1. **Intraday Microstructure (High-Frequency Context):**
   Scans the first 45 minutes of the trading session for Smart Money block orders and Volume Point of Control (VPOC) migrations to gauge institutional sentiment before executing swing trades.
2. **Short-Term Swing & Momentum (The Core Engine):**
   Optimized for a 3-to-15 day holding period. Leverages the LightGBM classifiers and ROC/MACD momentum matrices to ride the primary thrust of the prevailing market wave.
3. **Long-Term Macro (Regime Filtering & Weekend Staleness):**
   Monitors the 200-day EMA, FII/DII institutional flow, and India VIX to dictate the overarching **Hidden Markov Model (HMM) State**. Furthermore, the execution engine features a natively coded **96-hour data staleness threshold**, specifically engineered to gracefully maneuver over extended long weekends and market holidays without triggering false "stale data" panic vetos.

---

## 🆚 Why Agent Alpha?

| Capability | Generic Trading Bot | Agent Alpha |
|:--|:--|:--|
| **Signal Generation** | Single indicator (e.g., RSI crossover) | 15-model weighted ensemble |
| **Regime Awareness** | None (trades blindly in all conditions) | 4-state Hidden Markov Model |
| **Risk Firewall** | Basic static stop-loss | Explicit 12-rule zero-trust veto |
| **Position Sizing** | Fixed lots / constant capital | ATR + Dynamic Kelly Criterion scaling |
| **Database Architecture**| Local JSON / SQLite (corrupts easily) | Neon PostgreSQL Serverless DB with advanced SQLAlchemy pooling |
| **AI Integration** | Cloud API calls (OpenAI) | Local LLaMA 3.3 70B via Ollama (zero data leakage) |
| **Command Interfaces** | Web UI Only | Obsidian Web UI + Native macOS Menubar App + Telegram Bot |
| **Infrastructure** | Single python script | Dual-node Docker cluster + custom bash CI/CD (`deploy_to_dell.sh`) |

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

**Node 1 (Primary Executive Station - MacBook Pro):** The visualization and development terminal. The CEO interacts with the system here via the stunning Obsidian Glass UI and macOS Menubar app. Development, testing, and UI overhauls are built natively here.

**Node 2 (Sentinel Execution Node - Always-On Windows):** The absolute core of the operation. This secondary node runs the `docker-compose` stack containing the FastAPI backend, Neon DB links, Cron daemons, ML models, and the localized **Ollama (LLaMA 3.3 70B)** engine. Because Node 2 is "Always-On", the 8:00 AM pre-market scans and 3:45 PM execution cron-jobs trigger relentlessly without fail. 

**Flawless Deployment:** Pushing updates from Node 1 to Node 2 is executed instantaneously via the **`deploy_to_dell.sh`** script, which seamlessly connects to the Sentinel node via SSH, executes git pulls, rebuilds Docker images, and restarts the engine, completely bypassing manual Windows terminal interactions.

---

## 🧠 Core System Modules & Deep Dives

### 1. The 15-Model Quantitative Ensemble Engine

At the heart of Agent Alpha lies a weighted voting ensemble that outputs a continuous directional bias. Rather than relying on a single point of failure, the engine synthesizes signals from 15 distinct, uncorrelated models.

<div align="center">
  <img src=".github/assets/diagrams/ensemble.png" alt="15-Model Quantitative Ensemble Engine" width="100%" style="border-radius: 12px; box-shadow: 0 4px 30px rgba(0,255,136,0.15);" />
</div>

#### 📐 A. Technical Matrix (4 Models)
1.  **Kaufmans Adaptive Moving Average (KAMA/EMA)**
2.  **Regime-Adjusted RSI-14**
3.  **ATR Volatility Expansion**
4.  **Bollinger Squeeze Percentile**

#### 🌊 B. Momentum Matrix (3 Models)
5.  **MACD Histogram Acceleration**
6.  **Rate of Change (ROC-10)**
7.  **On-Balance Volume (OBV)**

#### 🧠 C. Machine Learning Layer (4 Models)
8.  **XGBoost Classifier:** Trained on historical OHLCV data using a walk-forward cross-validation window. Emits probabilities for Up, Down, and Flat over 5-day windows.
9.  **LightGBM Classifier:** Highly optimized, gradient-boosted decision tree layer natively handling complex engineered features.
10. **Lightweight Sequence Model:** A temporal sequence classifier designed to mimic LSTM networks, capturing cyclical sine-wave patterns.
11. **Short-Term Multilayer Perceptron (MLP)**

#### 🏦 D. Microstructure & Flow (4 Models)
12. **Smart Money / VPOC (Volume Point of Control)**
13. **StatArb Pairs Trading (Z-Score):** The `stat_arb.py` engine monitors highly cointegrated sector pairs (e.g., TCS vs INFY). Using verified rolling unit root testing, it triggers mean-reversion signals when the spread ratio deviates by more than $\pm2$ standard deviations.
14. **Institutional Flow (FII/DII Data)**
15. **Options Put-Call Ratio (PCR)**

---

## 🧱 The 12-Rule Hard Veto Firewall

Before any signal generated by the 15-Model Ensemble is allowed to hit the Paper Trading Arena, it is subjected to a zero-trust gauntlet. If a trade fails *even one* of these 12 rules, it is instantly vetoed and killed.

<div align="center">
  <img src=".github/assets/diagrams/veto.png" alt="12-Rule Hard Veto Firewall" width="100%" style="border-radius: 12px; box-shadow: 0 4px 30px rgba(255,0,60,0.15);" />
</div>

1. **VIX Threshold Breach:** Halts buys if India VIX spikes above 22 (Extreme Volatility).
2. **Missing API Data:** Kills execution if `yfinance` or FRED APIs return NULL vectors.
3. **Database Lock Detection:** Prevents trading if PostgreSQL transactions hang.
4. **Stale Price Data Guard:** Vetoes trades if the latest close price is older than 24 hours (excluding the 96-hour weekend gap exception).
5. **Impending Earnings Veto:** Halts trades if an equity is within 3 days of an earnings release.
6. **Sector Beta Overexposure:** Blocked by the Correlation Matrix if >3 active positions exist in the same sector.
7. **Aggressive FII Selling:** Vetoes bullish entries if Foreign Institutional Investors sold >₹2000Cr in the prior session.
8. **10L Capital Margin Breach:** Rejects trades if the allocated Kelly fraction exceeds available free cash.
9. **Extreme Z-Score Divergence:** Blocks execution if pairs trading spreads exceed $\pm4$ (statistical breakdown).
10. **Black Swan / Crisis Protocol Active:** Suspends all normal equity trading during declared market crashes.
11. **ATR Stop-Loss Proximity:** Rejects new entries if the calculated ATR stop-loss is dangerously close to major resistance.
12. **Ensemble Confidence < 60%:** Even if bullish, the trade is killed if the ML models aren't mathematically confident.

---

## 🚨 Crisis Regime Strategy Execution

During major market drawdowns, Agent Alpha dynamically switches into the **Crisis Regime**. This protects capital using a Safe Haven strategy while strategically accumulating the broader market at a discount. Validated completely via `test_crisis.py`.

<div align="center">
  <img src=".github/assets/diagrams/crisis.png" alt="Crisis Regime Strategy Execution" width="100%" style="border-radius: 12px; box-shadow: 0 4px 30px rgba(0,255,136,0.15);" />
</div>

### Execution Logic

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
To prevent over-leveraging, raw Kelly fractions ($K_{\text{raw}}$) are computed based on historical win rates ($W$) and profit factors ($R$):

$$ K_{\text{raw}} = W - \frac{1 - W}{R} $$

Unlike basic bots, Agent Alpha scales this fraction dynamically by the regime modifier ($M_{\text{regime}}$) and the global pre-market bias score ($B_{\text{global}}$):

$$ K_{\text{final}} = K_{\text{raw}} \times M_{\text{regime}} \times (1 + B_{\text{global}}) $$

---

## 🛠️ The "Self-Healing" Data Pipeline & Exhaustive Testing Suite

External APIs (`yfinance`, FRED) and Serverless Databases are inherently unstable. Agent Alpha is built with a resilient pipeline heavily scrutinized by a massive automated testing suite located in the `backend/` directory:

*   **Database Lock Mitigation (`test_db_hang.py`, `test_portfolio_hang.py`):** We systematically eliminated Neon Serverless deadlocks by engineering strict connection limits and recursion protection, verified by these intensive stress tests.
*   **The Execution Crucible (`test_arena_skip.py`):** Forces the Paper Trading arena to simulate executing hundreds of simultaneous trades to verify that slippage math and P&L updates never drop a transaction.
*   **Z-Score Validations (`test_zscore.py`):** Routinely verifies the standard deviation math for statistical arbitrage pairs, ensuring rolling unit roots never emit false positives.
*   **Pricing & Fallback Resilience (`test_prices.py`):** Verifies the `stock_fetcher` exponential backoff logic. If Yahoo Finance drops the connection, the system autonomously halts, waits, and falls back to cached SQLite data to prevent ML vectors from crashing.

---

## ⚙️ System Requirements & Deployment Topology

### Hardware Requirements (Sentinel Node)
*   **CPU:** 8-Core Processor (Apple Silicon M1/M2/M3, Intel Core i7, or AMD Ryzen 7)
*   **RAM:** 16GB Minimum (32GB+ Highly Recommended for LLaMA 3.3 70B execution in memory)
*   **Storage:** 50GB NVMe SSD
*   **Network:** Uninterrupted high-speed broadband 

### Dockerization Ignition Commands
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

**16. Agent Alpha Daily Briefing Bot**
*Comprehensive pre-market briefings delivering index sentiment, live portfolio updates, and top actionable AI stock targets directly to your phone.*
<img src="Screenshots/11.png" width="100%" style="border-radius: 8px; margin-bottom: 20px;">

<br>
<div align="center">
  <i>"The future of finance is not predicted. It is computed."</i><br/>
  <b>— Agent Alpha</b>
</div>
