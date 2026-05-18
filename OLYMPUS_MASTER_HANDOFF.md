# 🏛️ AGENT ALPHA v4.0 — OLYMPUS MASTER HANDOFF SPEC

> **Purpose:** This document is the SINGLE SOURCE OF TRUTH for building Agent Alpha v4.0.
> Any AI model (Gemini, Claude, etc.) should be able to follow this spec and produce
> correct, working code without requiring additional context or clarification.

---

## TABLE OF CONTENTS

1. [Device Allocation: Mac vs Windows](#1-device-allocation)
2. [The Self-Learning Engine](#2-the-self-learning-engine)
3. [Build Order & Phase Specs](#3-build-order)
4. [Phase 1: Paper Trading Arena](#phase-1-the-arena)
5. [Phase 2: Self-Learning Feedback Loop](#phase-2-self-learning)
6. [Phase 3: Model Championship](#phase-3-championship)
7. [Phase 4: Sentinel (Windows Laptop)](#phase-4-sentinel)
8. [Phase 5: Weekend War Room PDF](#phase-5-war-room)
9. [Windows Laptop Setup Guide](#windows-setup)

---

## 1. DEVICE ALLOCATION

### MacBook (Portable — goes to office)

| Component | Details |
|-----------|---------|
| FastAPI Backend (`backend/main.py`) | Runs locally via `venv/bin/python3 -m uvicorn main:app` |
| PWA Dashboard | Served by FastAPI at `localhost:8000` |
| Menu Bar Widget (`backend/menubar_app.py`) | Native macOS tray app via `rumps` |
| Arena Engine | API endpoints + frontend tab (logic runs here OR via GitHub Actions) |
| Championship Leaderboard | Frontend tab + API endpoints |
| War Room PDF Generator | Triggered by GitHub Actions on Saturdays |

### Windows Laptop (Home — always on, 24/7)

| Component | Details |
|-----------|---------|
| Ollama Server | Runs `llama3.1:8b` (full 16GB available since NAS paused) |
| Sentinel Daemon (`sentinel.py`) | Polls RSS feeds every 5 min, classifies via Ollama |
| WebSocket Server (port 9090) | Pushes alerts to Mac's menu bar widget |
| SQLite alerts database | Stores all classified headlines locally |

> **Why Llama 3.1 8B now (not Phi-3)?** Since NAS is paused, full 16GB RAM is available.
> Llama 3.1 8B needs ~8GB, leaving 8GB for Windows + Sentinel daemon. This gives us
> ~91% classification accuracy vs Phi-3's ~88%.

### Cloud (GitHub Actions + Render)

| Component | Details |
|-----------|---------|
| Daily Briefing | GitHub Actions cron: 8 AM + 3:45 PM IST (existing `main.yml`) |
| Arena Auto-Execute | NEW GitHub Actions cron: 9:20 AM IST (after market opens) |
| Arena Auto-Close | NEW GitHub Actions cron: 3:35 PM IST (market close check) |
| War Room PDF | NEW GitHub Actions cron: Saturday 10 AM IST |
| Render Backend | Cloud deployment for mobile access |

---

## 2. THE SELF-LEARNING ENGINE

This is the core innovation. The system learns from every mistake automatically.

### The 5-Layer Learning Loop

```
LAYER 1: RECORD EVERYTHING
  Every signal stores: model_votes_json, regime, VIX, sector, RVOL, time_of_day, day_of_week

LAYER 2: RESOLVE OUTCOMES (daily at 4 PM)
  After 5 trading days, check: did the stock move as predicted?
  Tag each prediction as WIN / LOSS / FLAT

LAYER 3: MINE ERROR PATTERNS (weekly on Sunday)
  SQL analysis discovers patterns like:
  - "Options Flow model is 35% accurate in Crisis regime"
  - "System loses 70% of trades entered on Fridays"
  - "Momentum model fails when VIX > 22"

LAYER 4: AUTO-GENERATE RULES
  Discovered patterns become conditional rules stored in `learned_rules` table:
  - IF regime='crisis' → set options_flow weight to 5 (from 25)
  - IF day_of_week='Friday' AND conviction != 'ULTRA' → SKIP trade
  - IF VIX > 22 → halve momentum weight

LAYER 5: EVOLVE WEIGHTS
  Instead of static weights, use REGIME-CONDITIONAL weights that update monthly:
  - low_vol_uptrend: {transformer: 28, technicals: 20, regime: 15, ...}
  - crisis: {regime: 40, transformer: 10, options_flow: 5, ...}
  These evolve based on per-regime accuracy data.
```

### Confidence Calibration

Track: "When the system says 70% confidence, is it actually right 70% of the time?"

```
calibration_buckets:
  50-60% confidence → actual win rate: ??%
  60-70% confidence → actual win rate: ??%
  70-80% confidence → actual win rate: ??%
  80-90% confidence → actual win rate: ??%
```

If the system says 75% but actual is 55%, it learns to multiply by a calibration factor
(55/75 = 0.73). This prevents overconfidence.

---

## 3. BUILD ORDER

**CRITICAL: Build in this exact order. Each phase depends on the previous one.**

| Phase | What | Where to Build | Depends On |
|-------|------|----------------|------------|
| 1 | Paper Trading Arena | MacBook (backend/) | Nothing |
| 2 | Self-Learning Feedback Loop | MacBook (backend/) | Phase 1 |
| 3 | Model Championship Leaderboard | MacBook (backend/ + frontend/) | Phase 2 |
| 4 | Sentinel Daemon | Windows Laptop | Phase 1-3 done |
| 5 | Weekend War Room PDF | MacBook + GitHub Actions | Phase 1-3 done |

---

## PHASE 1: THE ARENA

### Files to Create

```
backend/
  arena/
    __init__.py
    paper_trading.py      # Core engine: execute, close, track trades
    trade_autopsy.py      # Post-mortem analysis for each closed trade
    arena_scheduler.py    # Daily cron logic (what to buy/sell today)
```

### Database Tables (add to `backend/database.py` → `init_db()`)

```sql
CREATE TABLE IF NOT EXISTS paper_trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    trade_type TEXT NOT NULL DEFAULT 'BUY',
    status TEXT DEFAULT 'OPEN',
    signal_date TEXT NOT NULL,
    entry_date TEXT NOT NULL,
    entry_price REAL NOT NULL,
    quantity INTEGER NOT NULL,
    position_value REAL NOT NULL,
    stop_loss REAL NOT NULL,
    target_price REAL NOT NULL,
    risk_reward_ratio REAL,
    exit_date TEXT,
    exit_price REAL,
    exit_reason TEXT,
    gross_pnl REAL,
    fees REAL,
    net_pnl REAL,
    return_pct REAL,
    regime_at_entry TEXT,
    ensemble_score REAL,
    conviction TEXT,
    model_votes_json TEXT,
    veto_status TEXT,
    autopsy_json TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS paper_portfolio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT UNIQUE NOT NULL,
    cash REAL NOT NULL,
    holdings_value REAL NOT NULL,
    total_equity REAL NOT NULL,
    open_positions INTEGER,
    daily_return_pct REAL,
    cumulative_return_pct REAL,
    drawdown_from_peak_pct REAL,
    benchmark_nifty_return_pct REAL,
    created_at TEXT DEFAULT (datetime('now'))
);
```

### API Endpoints to Add (in `backend/main.py`)

```python
# Arena endpoints
@app.get("/api/arena/portfolio")     # Current paper portfolio state
@app.get("/api/arena/trades")        # All trades (open + closed)
@app.get("/api/arena/equity-curve")  # Daily equity values for charting
@app.get("/api/arena/stats")         # Win rate, Sharpe, drawdown, etc.
@app.post("/api/arena/execute")      # Manually trigger arena execution
```

### Core Logic: `paper_trading.py`

```python
INITIAL_CAPITAL = 1_000_000  # ₹10 Lakh
MAX_POSITIONS = 5
SLIPPAGE_PCT = 0.003         # 0.3%
BROKERAGE_PCT = 0.001        # 0.1%
STT_PCT = 0.001              # 0.1%
MAX_HOLD_DAYS = 15           # Timeout
MIN_CONVICTION = "HIGH"      # Only HIGH or ULTRA trades

def execute_daily_arena():
    """Called daily at 9:20 AM IST via GitHub Actions or cron."""
    # 1. Get current paper portfolio state from DB
    # 2. Check open positions for SL/Target hits using today's OPEN price
    # 3. Close any positions that hit SL, Target, or 15-day timeout
    # 4. Run trade autopsy for each closed position
    # 5. If open_positions < MAX_POSITIONS:
    #    a. Run screener (reuse existing get_technical_analysis)
    #    b. Filter for conviction >= MIN_CONVICTION
    #    c. Calculate position size using existing Kelly engine
    #    d. Execute at today's OPEN + SLIPPAGE
    #    e. Store trade with full context (model_votes, regime, VIX, etc.)
    # 6. Snapshot portfolio equity to paper_portfolio table
    # 7. Send summary to Telegram
```

### Frontend: New "Arena" Tab

Add to sidebar in `index.html` after existing tabs. The tab has 4 sections:
1. **Live Positions** — Cards showing open trades with real-time P&L
2. **Equity Curve** — Chart.js line chart: Arena equity vs Nifty 50 buy-and-hold
3. **Trade History** — Sortable table of closed trades with WIN/LOSS badges
4. **Monthly Stats** — Calendar heatmap (green=profit day, red=loss day)

### GitHub Actions Addition (`.github/workflows/main.yml`)

```yaml
  arena-execute:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    schedule:
      - cron: '50 3 * * 1-5'   # 9:20 AM IST
      - cron: '5 10 * * 1-5'   # 3:35 PM IST
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.10', cache: 'pip' }
      - run: pip install -r requirements.txt
      - run: cd backend && python -m arena.arena_scheduler
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

---

## PHASE 2: SELF-LEARNING

### Files to Create

```
backend/
  arena/
    self_learner.py       # Error pattern mining + rule generation
    weight_evolver.py     # Regime-conditional weight optimization
    calibrator.py         # Confidence calibration tracker
```

### Database Tables

```sql
CREATE TABLE IF NOT EXISTS prediction_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    signal_date TEXT NOT NULL,
    signal_type TEXT,
    confidence REAL,
    ensemble_score REAL,
    model_votes_json TEXT,
    regime TEXT,
    vix_level REAL,
    day_of_week TEXT,
    sector TEXT,
    rvol REAL,
    outcome TEXT,                    -- 'WIN', 'LOSS', 'FLAT', NULL (pending)
    actual_return_pct REAL,
    resolved_date TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS learned_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_type TEXT NOT NULL,          -- 'WEIGHT_OVERRIDE', 'TRADE_SKIP', 'CONFIDENCE_ADJUST'
    condition_json TEXT NOT NULL,     -- {"regime": "crisis", "model": "options_flow"}
    action_json TEXT NOT NULL,        -- {"set_weight": 5} or {"skip": true}
    confidence REAL,                 -- How confident are we in this rule (based on sample size)
    sample_size INTEGER,
    discovered_date TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS regime_weights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    regime TEXT NOT NULL,
    weights_json TEXT NOT NULL,       -- {"transformer": 28, "technicals": 20, ...}
    accuracy_data_json TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS calibration_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    confidence_bucket TEXT NOT NULL,  -- '50-60', '60-70', '70-80', '80-90'
    predicted_win_rate REAL,
    actual_win_rate REAL,
    sample_size INTEGER,
    calibration_factor REAL,         -- actual/predicted
    updated_at TEXT DEFAULT (datetime('now'))
);
```

### Key Logic: `self_learner.py`

```python
def mine_error_patterns():
    """Run weekly. Discovers which conditions cause losses."""
    # Query: GROUP BY regime, model WHERE outcome = 'LOSS'
    # For each model × regime combination:
    #   Calculate accuracy = wins / (wins + losses)
    #   If accuracy < 45% AND sample_size >= 20:
    #     Generate rule: suppress this model in this regime
    #     Store in learned_rules table
    
    # Query: GROUP BY day_of_week WHERE outcome = 'LOSS'
    # If Friday win_rate < 40%:
    #   Generate rule: skip non-ULTRA trades on Fridays
    
    # Query: Find VIX threshold where accuracy drops
    # Bin VIX into ranges, find breakpoint

def apply_learned_rules(signal, context):
    """Called during signal generation. Applies discovered rules."""
    # Load active rules from learned_rules table
    # For each rule, check if current context matches condition
    # Apply action (suppress weight, skip trade, adjust confidence)
```

### Integration Point

In `backend/analysis/ensemble.py`, modify `EnsembleVoter.__init__()`:

```python
def __init__(self):
    self.weights = self._load_regime_weights()  # Instead of static dict
    
def _load_regime_weights(self):
    """Load regime-conditional weights from DB. Fall back to defaults."""
    # Try loading from regime_weights table
    # If no data yet, return static defaults
    # As self_learner.py populates the table, weights evolve
```

---

## PHASE 3: CHAMPIONSHIP

### Files to Create

```
backend/
  arena/
    championship.py       # Model leaderboard tracking
```

### Wire Into Existing Code

The existing `backend/analysis/alpha_decay.py` (AlphaDecayMonitor) and 
`backend/analysis/accuracy.py` are already built but NOT connected to the live pipeline.

**Connection points:**
1. In `daily_job.py` line ~250: After `db.save_ensemble_signal(symbol, ensemble)`,
   also save individual model votes to `prediction_log`
2. In `accuracy.py` `resolve_pending_signals()`: After resolving, also update
   the AlphaDecayMonitor with the outcome per model
3. New API: `@app.get("/api/championship")` returns the leaderboard

### Frontend

Add a "Championship" section inside the existing Accuracy tab:
- Table showing all 8 models ranked by 60-day rolling accuracy
- Sparkline trend per model (unicode: ▃▅▆▇)
- Status badge: HEALTHY / DECAYING / SUSPENDED
- Current weight vs baseline weight

---

## PHASE 4: SENTINEL (Windows Laptop)

### Files to Create (on Windows laptop)

```
sentinel/
    sentinel.py           # Main daemon: poll feeds → classify → alert
    feed_poller.py        # RSS + NSE + BSE data fetchers
    ws_server.py          # WebSocket server for pushing alerts to Mac
    config.py             # Ollama URL, feed URLs, alert thresholds
    requirements.txt      # feedparser, websockets, aiohttp, requests
```

### Sentinel Classifier Prompt (optimized for speed)

```
You are a financial news classifier for Indian stock market (NSE/BSE).
CLASSIFY: "{headline}"
Reply ONLY with this JSON, nothing else:
{"m":true/false,"s":1-10,"t":["SYMBOL"],"c":"EARNINGS|REGULATORY|MACRO|INSIDER|SECTOR","r":"10 words max"}
```

> Short key names ("m" not "market_moving") reduce token count → faster inference.

### Alert Severity Thresholds

| Category | Alert if severity >= |
|----------|---------------------|
| MACRO | 5 |
| REGULATORY | 6 |
| EARNINGS | 7 |
| INSIDER | 7 |
| SECTOR | 8 |

### Mac Integration

In `backend/menubar_app.py`, add a WebSocket client thread:
```python
import websockets, asyncio
# Connect to ws://192.168.x.x:9090 (Windows laptop IP)
# On message: update menu bar badge count, store alert
```

### Windows Setup Commands

```powershell
# 1. Install Ollama
winget install Ollama.Ollama

# 2. Pull model (one-time ~4.7GB download)
ollama pull llama3.1:8b

# 3. Test
ollama run llama3.1:8b "Classify: RBI cuts repo rate by 25 bps"

# 4. Install Python + deps
pip install feedparser websockets aiohttp requests

# 5. Create Windows Task Scheduler entry for sentinel.py auto-start on boot
```

---

## PHASE 5: WAR ROOM PDF

### Files to Create

```
backend/
  reports/
    __init__.py
    war_room.py           # PDF generation using fpdf2 + matplotlib
    charts.py             # Equity curve, heatmap, model bar charts
```

### Dependencies

```
pip install fpdf2 matplotlib
```

### GitHub Actions (Saturday 10 AM IST)

```yaml
  war-room:
    runs-on: ubuntu-latest
    schedule:
      - cron: '30 4 * * 6'  # Saturday 10 AM IST
    steps:
      - run: cd backend && python -m reports.war_room
      # Sends PDF to Telegram using sendDocument API
```

### PDF Sections

1. **Arena Performance** — Equity curve chart, weekly/cumulative returns vs Nifty
2. **Trade Log** — This week's trades with autopsy summaries
3. **Model Championship** — Leaderboard table + accuracy trends
4. **Regime Analysis** — Current regime, crisis probability, VIX trend
5. **Sentinel Highlights** — Top 5 most impactful news events this week
6. **Next Week Outlook** — Macro calendar, regime forecast, watchlist

---

## EXISTING CODEBASE REFERENCE

### Key Files & Their Roles (for any AI model picking this up)

| File | Role | Lines |
|------|------|-------|
| `backend/main.py` | FastAPI app, all API endpoints | 989 |
| `backend/database.py` | SQLite/Postgres, all DB operations | 622 |
| `backend/config.py` | Nifty 50 symbols, sectors, settings | 236 |
| `backend/bot/daily_job.py` | Daily pipeline: data→ensemble→telegram | 376 |
| `backend/analysis/ensemble.py` | 8-model weighted voter | 322 |
| `backend/analysis/technical.py` | KAMA, ADX, RSI divergence (Model 1) | 546 |
| `backend/analysis/transformer_engine.py` | Sequence model (Model 2) | 291 |
| `backend/analysis/ml_engine.py` | LightGBM classifier | 407 |
| `backend/analysis/sentiment_engine.py` | VADER + FinBERT + lexicon (Model 4) | 401 |
| `backend/analysis/regime.py` | HMM 4-state regime classifier | 335 |
| `backend/analysis/veto_engine.py` | 12-rule hard veto firewall | 309 |
| `backend/analysis/position_sizing.py` | Kelly Criterion sizing | ~300 |
| `backend/analysis/backtest_engine.py` | Walk-forward backtester | 236 |
| `backend/analysis/alpha_decay.py` | Model accuracy decay monitor | 210 |
| `backend/analysis/accuracy.py` | Signal outcome tracking | 245 |
| `backend/menubar_app.py` | macOS menu bar widget (rumps) | ~170 |
| `frontend/index.html` | PWA dashboard | ~500 |
| `frontend/css/styles.css` | All styling | ~2000 |
| `.github/workflows/main.yml` | Daily cron jobs | ~50 |
| `.env` | API keys (Telegram, Gemini, DB) | 9 |

### Key Existing Functions to Reuse

```python
# Screener — reuse for Arena signal generation
from analysis.technical import get_technical_analysis, screen_stocks

# Regime — reuse for context tagging
from analysis.regime import get_current_market_regime

# Position Sizing — reuse for Arena quantity calculation
from analysis.position_sizing import calculate_position_size

# Ensemble — reuse for model votes
from analysis.ensemble import get_ensemble_analysis

# Backtest costs — reuse slippage/fee model
from analysis.backtest_engine import backtester

# Veto — reuse for Arena trade filtering
from analysis.veto_engine import veto_engine

# Alpha Decay — wire into Championship
from analysis.alpha_decay import AlphaDecayMonitor

# Accuracy — wire into self-learning
from analysis.accuracy import resolve_pending_signals, get_accuracy_stats

# Telegram — reuse for Arena notifications
from bot.daily_job import send_telegram_sync

# Stock data — reuse for price checks
from data.stock_fetcher import download_ohlcv, get_ltp
```

### Database Pattern (MUST follow)

All DB operations in this codebase use this pattern:
```python
import database as db

# For queries that return data:
rows = db.db_execute("SELECT * FROM table WHERE col = ?", (value,))

# For inserts/updates:
db.db_execute("INSERT INTO table (col) VALUES (?)", (value,))

# The db_execute function handles both SQLite (local) and Postgres (cloud)
# It auto-converts ? to %s for Postgres
```

### Frontend Pattern (MUST follow)

All frontend tabs follow this pattern in `index.html`:
```html
<div class="tab-content" id="tab-arena" style="display:none;">
    <!-- Content here -->
</div>
```

With corresponding sidebar button and JavaScript tab switcher in the existing code.

---

## INSTRUCTIONS FOR ANY AI MODEL CONTINUING THIS WORK

1. **Read this document FIRST** before writing any code
2. **Build in the exact phase order** (1→2→3→4→5)
3. **Reuse existing functions** — do NOT rewrite what already exists
4. **Follow the existing DB pattern** using `db.db_execute()`
5. **Follow the existing frontend pattern** for new tabs
6. **Test each phase** before moving to the next
7. **All new backend files** go in `backend/arena/` or `backend/reports/`
8. **All Sentinel files** are built separately on the Windows laptop
9. **Bump cache version** in `index.html` and `sw.js` after frontend changes
10. **The .env file** already has all needed API keys (Telegram, Gemini, DB)

### Phase 1 Acceptance Criteria
- [ ] `paper_trades` and `paper_portfolio` tables created
- [ ] Arena can execute a paper trade from screener signals
- [ ] Arena checks SL/Target/Timeout for open positions daily
- [ ] Equity curve data stored daily with Nifty benchmark
- [ ] Frontend "Arena" tab shows positions, equity chart, trade history
- [ ] Telegram notification on each trade open/close
- [ ] Trade autopsy generated for each closed trade

### Phase 2 Acceptance Criteria
- [ ] Every signal stores full context in `prediction_log`
- [ ] `self_learner.py` discovers error patterns from accumulated data
- [ ] `learned_rules` table stores auto-generated conditional rules
- [ ] `regime_weights` table stores per-regime model weights
- [ ] Ensemble voter loads regime-conditional weights dynamically
- [ ] Confidence calibration tracks predicted vs actual win rates

### Phase 3 Acceptance Criteria
- [ ] Model leaderboard API returns all 8 models ranked by 60d accuracy
- [ ] Frontend shows championship table with sparkline trends
- [ ] Models automatically downweighted when accuracy drops >8%
- [ ] Models suspended when accuracy drops >15%

### Phase 4 Acceptance Criteria
- [ ] Ollama running on Windows laptop with Llama 3.1 8B
- [ ] Sentinel polls 5+ RSS feeds every 5 minutes
- [ ] LLM classifies each headline in <1 second
- [ ] Telegram alert fires for severity >= threshold
- [ ] WebSocket pushes alerts to Mac menu bar widget
- [ ] Alert history stored in local SQLite

### Phase 5 Acceptance Criteria
- [ ] PDF generated with matplotlib charts + fpdf2
- [ ] Contains all 6 sections (Arena, Trades, Championship, Regime, Sentinel, Outlook)
- [ ] Auto-sent to Telegram as document every Saturday 10 AM IST
- [ ] GitHub Actions workflow triggers correctly
