# AGENT ALPHA v2.0 — MASTER BUILD SPECIFICATION
### Complete Prompt for Antigravity | Classification: Maximum Priority

---

## MISSION STATEMENT

You are being asked to rebuild and massively upgrade a systematic quantitative trading engine called **Agent Alpha** — originally built for Indian equity markets (NSE/BSE). The current system is a solid momentum screener. Your task is to evolve it into the most accurate, most robust, most institutionally rigorous systematic trading system ever built for Indian equity markets. This is not incremental improvement. This is a full architectural overhaul. Build every layer described below — completely, correctly, and without shortcuts.

The current engine lives in `backend/analysis/technical.py`. You will extend, refactor, and augment it with everything described in this document.

---

## ARCHITECTURE OVERVIEW

The upgraded system consists of 6 layers. Every layer must be built. No layer is optional.

```
LAYER 1 → Data Foundation (India-specific + Global)
LAYER 2 → Signal Generation (Ensemble of 6 independent models)
LAYER 3 → Regime Intelligence (Know what market you're in)
LAYER 4 → ML Decision Engine (XGBoost now → RL agent later)
LAYER 5 → Risk & Execution (Where money is protected)
LAYER 6 → Continuous Improvement (System that never decays)
```

---

## LAYER 1 — DATA FOUNDATION

### 1.1 Existing Data (Keep and Upgrade)
- End-of-Day OHLCV price data for NSE/BSE equities
- Ensure all price data is **adjusted for corporate actions** (splits, bonuses, dividends). Any unadjusted price data will corrupt every downstream calculation.
- Store raw + adjusted versions separately. Never overwrite raw.

### 1.2 NEW: FII / DII Daily Flow Data [HIGHEST PRIORITY — FREE SOURCE]
This is the single most powerful freely available signal in Indian markets.

**Source:** NSE publishes this daily at `https://www.nseindia.com/market-data/live-market-statistics`
- Scrape and store daily: FII Net Buy/Sell (Equity), DII Net Buy/Sell (Equity)
- Build a rolling 5-day and 20-day cumulative flow metric for both FII and DII
- Signal construction:
  - `fii_flow_score`: If FII net positive for 3+ consecutive days AND cumulative 5-day > ₹2000Cr → +2 points; if FII net negative for 3+ consecutive days → -2 points; neutral → 0
  - `dii_flow_score`: Same logic for DII
  - `institutional_consensus`: If both FII and DII are net buyers → strong bullish confirmation; if divergent → reduce signal confidence by 30%
- **Hard Rule:** When FII net selling > ₹5000Cr on any single day, suppress ALL buy signals across the entire universe for the next 2 trading days regardless of technical score.

### 1.3 NEW: Options Chain Data [CRITICAL for Range Prediction]
**Source:** NSE Options chain API (available via NSE website scraping or data vendor)
- Pull daily for Nifty 50 index and for individual stock options where available
- Extract: Strike prices, Call OI, Put OI, Call IV, Put IV, Call LTP, Put LTP
- **Calculate Max Pain:** The strike where maximum options contracts expire worthless. This is a gravitational pull on price in the last 3 days before expiry. Formula: For each strike, calculate total monetary loss to all option buyers if price expires at that strike. Max Pain = strike with minimum total payout from seller's perspective.
- **Calculate ATM Straddle Price:** ATM Call LTP + ATM Put LTP = implied expected daily move. Use this to replace or heavily weight the ATR-based range prediction.
  - `implied_daily_range = (ATM_straddle_price / spot_price) × 100` → this is your 1σ expected move
  - Expected range: `Close ± (implied_daily_range × Close)` — this replaces `Close ± ATR` for range prediction
  - Options-implied range has proven 78–84% accuracy vs ATR's 65–70%
- **Calculate Put-Call Ratio (PCR):** Total Put OI / Total Call OI
  - PCR > 1.5 = oversold / potential reversal signal
  - PCR < 0.7 = overbought / potential reversal signal
  - PCR 0.8–1.2 = neutral market
  - Extreme PCR readings (>2.0 or <0.5) indicate capitulation or euphoria — treat as contrarian signal

### 1.4 NEW: Shareholding Pattern & Promoter Pledging [HARD VETO DATA]
**Source:** BSE/NSE quarterly shareholding filings (available via BSE API or scraping)
- Pull quarterly shareholding data for all stocks in universe
- Track: Promoter holding %, Promoter pledged shares %, FII holding %, MF holding %
- **Hard Veto Rule 1:** If promoter pledging > 40% AND pledging has increased quarter-over-quarter → BLOCK all buy signals for this stock. No technical score overrides this. Set a `pledging_veto = True` flag.
- **Hard Veto Rule 2:** If promoter pledging has increased by > 10% in a single quarter → BLOCK for 2 quarters.
- **Positive Signal:** If FII holding has increased QoQ AND MF holding has increased QoQ simultaneously → add +5 to the base score for that stock (institutional accumulation confirmation).

### 1.5 NEW: Bulk & Block Deal Data [FREE, HIGHLY PREDICTIVE]
**Source:** NSE publishes bulk and block deals daily
- Scrape daily bulk deal and block deal tables
- A bulk deal > 0.5% of company equity in a single session is a strong directional signal
- If bulk deal is on the buy side by a known institution → +3 to score for 3 days
- If bulk deal is on the sell side by a promoter → -3 to score, flag for review

### 1.6 NEW: Pre-Market Intelligence Layer [Gap Risk Mitigation]
Pull the following every morning before market open at 8:00 AM IST:
- **SGX Nifty Futures:** Current premium/discount to previous Nifty close = gap indicator
- **Dow Jones Futures / S&P 500 Futures:** Overnight US market direction
- **USD/INR Futures:** Currency stress indicator (sharp INR depreciation = FII selling pressure)
- **Crude Oil Futures:** India is a major oil importer; crude spike > 3% overnight = negative regime signal
- **Build Pre-Market Regime Score:**
  - SGX Nifty gap > +0.5% AND Dow futures positive → Pre-market bullish (+1)
  - SGX Nifty gap > +1.5% → Strong gap-up, widen expected range upward by 0.5× ATR
  - SGX Nifty gap < -0.5% AND Dow futures negative → Pre-market bearish (-1)
  - SGX Nifty gap < -1.5% → Strong gap-down, suppress buy signals, widen range downward
  - USD/INR depreciation > 0.5% overnight → FII selling pressure likely, reduce long exposure -1

### 1.7 NEW: NSE/BSE Corporate Announcements Feed
- Scrape the official exchange announcement feeds daily (BSE: `https://www.bseindia.com/corporateaction/`, NSE: corporate actions endpoint)
- Build an `earnings_blackout` flag: Any stock with an earnings announcement, board meeting, or AGM within the next 5 trading days → reduce position sizing by 50%, widen stop losses
- Any stock with a pending regulatory filing or SEBI notice → add warning flag to output

### 1.8 NEW: Delivery Percentage Data [India-Specific Conviction Signal]
**Source:** NSE publishes daily delivery percentage for every stock
- High delivery % (>60%) = strong conviction buying — buyers intend to hold, not just trade
- Low delivery % (<20%) = speculative/intraday activity, less reliable signal
- `delivery_score`: delivery% > 65% → +2 points; delivery% 40–65% → 0; delivery% < 25% → -1

---

## LAYER 2 — SIGNAL GENERATION (ENSEMBLE OF 6)

The system must run 6 independent signal models in parallel. Each model votes on direction (BUY / SELL / NEUTRAL) with a confidence score 0–100. Final signal is determined by ensemble logic described at the end of this section.

### Model 1: Refined Momentum/Trend Model (Existing — Upgrade)
Keep the existing EMA/MACD/RSI scoring system. Apply the following upgrades:
- Replace static EMA lengths with **adaptive EMAs** that adjust period based on ATR volatility. In high-volatility regimes, lengthen the period (reduces whipsaws). In low-volatility regimes, shorten (captures moves faster).
- Add **MACD Histogram Rate of Change:** Not just whether histogram is positive, but whether it's accelerating. Accelerating positive histogram = stronger signal.
- Add **RSI Divergence Detection:** Price makes new high but RSI makes lower high → bearish divergence → reduce or flip signal. Price makes new low but RSI makes higher low → bullish divergence → add to score.
- Add **ADX (Average Directional Index):** ADX > 25 = trending market (momentum signals valid), ADX < 20 = choppy market (suppress momentum signals, do not trade).
- Weight in ensemble: 20%

### Model 2: Order Flow Imbalance (OFI) Model [NEW]
Order flow measures whether aggressive buyers or aggressive sellers are dominant.
- **For NSE tick data:** Calculate `OFI = (Buy volume at ask - Sell volume at bid) / Total volume` for each 15-minute interval
- `OFI > +0.3` = aggressive buying pressure → BUY signal
- `OFI < -0.3` = aggressive selling pressure → SELL signal
- Build a cumulative OFI over the last 30 minutes of each trading session — end-of-day OFI direction is a strong predictor of next-day gap direction
- If tick-level data unavailable: approximate using `(Close - Open) / (High - Low)` as a normalized OFI proxy
- Weight in ensemble: 20%

### Model 3: Options-Implied Intelligence Model [NEW]
- **Range Prediction:** Use ATM straddle price (from Layer 1.3) as the primary range predictor. Replace ATR in all range calculations.
- **Directional Bias from Skew:** If 5% OTM Calls have higher IV than 5% OTM Puts → market expects upside → call skew bullish; if Put IV > Call IV → put skew bearish
- **OI Buildup Direction:** If Call OI increasing at strikes above current price → resistance forming; Put OI increasing below → support forming. Net OI accumulation direction = directional signal.
- **Max Pain Pull:** In the last 3 days before expiry, score is biased toward Max Pain strike (price gravitates toward it). Calculate distance from current price to Max Pain and direction of that pull.
- Weight in ensemble: 15%

### Model 4: News Sentiment NLP Model [NEW]
- Deploy **FinBERT** (open-source financial NLP model, available at `ProsusAI/finbert` on HuggingFace) fine-tuned for financial sentiment classification: POSITIVE / NEGATIVE / NEUTRAL
- **Input sources:** NSE/BSE announcements, Economic Times headlines, Moneycontrol news feed (scrape RSS feeds), Bloomberg India headlines
- For each stock, aggregate the last 24 hours of news headlines into a sentiment score:
  - `sentiment_score = weighted_avg(finbert_scores)` where more recent news is weighted higher
  - Strongly Negative (score < -0.5) → SELL signal, flag for gap risk
  - Strongly Positive (score > 0.5) → BUY confirmation
  - Neutral → no contribution
- **Sector-level sentiment:** If >70% of news for a sector is negative, suppress buy signals for all stocks in that sector regardless of individual score.
- Weight in ensemble: 15%

### Model 5: FII/DII Institutional Flow Model [NEW — India-Specific]
This is unique to Indian markets and is extremely powerful:
- Use the daily FII/DII data from Layer 1.2
- **Trend in flows (more important than single day):**
  - FII net buyer for 5+ consecutive days → Strong institutional accumulation → BUY +3
  - FII net buyer for 10+ consecutive days → Very strong accumulation → BUY +5
  - FII net seller for 5+ consecutive days → Distribution → SELL -3
  - DII acting as counterbalance to FII (buying when FII sells heavily) → market finding support → NEUTRAL / reduced volatility
- **Sector-specific FII flow:** If available, use sector-level FII data. FII buying heavily in IT sector → boost IT stock scores.
- **Relative flow momentum:** Is FII flow accelerating or decelerating? Accelerating buying > steady buying.
- Weight in ensemble: 15%

### Model 6: Volume Profile & Market Microstructure Model [NEW]
- **VWAP (Volume Weighted Average Price):** Price above VWAP = institutional buying zone; price below VWAP = selling pressure. `price / VWAP - 1` as a normalized signal.
- **Volume Profile (Price at Volume):** Calculate the Point of Control (POC) — the price level with the highest traded volume over the past 20 days. POC acts as a magnet. Price approaching POC from below = resistance. Price bouncing off POC = support confirmed.
- **Delivery Percentage Score:** From Layer 1.8 data, incorporate `delivery_score` here.
- **Relative Volume (RVOL):** Today's volume vs 20-day average volume. RVOL > 1.5 with price up = institutional accumulation; RVOL > 1.5 with price down = distribution (strong SELL signal).
- **Unusual Volume Detection:** Any stock with RVOL > 3.0 on any day in the past 5 days — flag as potentially being accumulated or distributed. Directional signal depends on price action.
- Weight in ensemble: 15%

### Ensemble Decision Logic
After all 6 models produce their signal (BUY/SELL/NEUTRAL) and confidence (0–100):

```python
# Weighted ensemble score
ensemble_score = sum(model_confidence[i] × model_weight[i] × model_direction[i])
# where direction: BUY=+1, SELL=-1, NEUTRAL=0

# Agreement count
buy_votes = count(models where direction == BUY)
sell_votes = count(models where direction == SELL)

# Signal classification:
if buy_votes >= 5 and ensemble_score > 70:
    signal = "ULTRA HIGH CONVICTION BUY"  # Size up to 1.5× Kelly
elif buy_votes >= 4 and ensemble_score > 55:
    signal = "HIGH CONVICTION BUY"         # Full Kelly size
elif buy_votes >= 3 and ensemble_score > 40:
    signal = "MODERATE BUY"                # 0.5× Kelly size
elif buy_votes <= 1 or ensemble_score < 20:
    signal = "STAND ASIDE"                 # No trade
# Mirror for SELL signals
```

**Critical Rule:** If ANY hard veto is triggered (promoter pledging, earnings blackout, FII mass selling), the signal is overridden to STAND ASIDE regardless of ensemble score. Hard vetoes cannot be unlocked by technical signals.

---

## LAYER 3 — REGIME INTELLIGENCE

The system must know what kind of market it is operating in at all times. Different regimes require completely different signal thresholds and position sizing. This is the layer that saves you from catastrophic losses in bear markets.

### 3.1 Hidden Markov Model (HMM) Regime Classifier
Train a 4-state HMM on the following Nifty 50 features:
- Daily returns
- Rolling 20-day realized volatility
- VIX level and 5-day change in VIX
- Advance/Decline ratio (breadth)
- Nifty 50 distance from 200-day EMA (as %)

**4 Regime States:**

**State 1: Low-Vol Uptrend (Home Turf)**
- Characteristics: VIX < 15, Nifty above 200 EMA, A/D ratio > 1.2, low realized vol
- Action: Full aggression. All 6 models active. Standard Kelly sizing. Momentum signals at full weight.
- Expected win rate: 68–73%

**State 2: High-Vol Uptrend (Cautious Bull)**
- Characteristics: VIX 15–25, Nifty above 200 EMA but choppy, A/D ratio mixed
- Action: Reduce position sizes to 60% of Kelly. Widen stop losses by 1.5×. Only take HIGH CONVICTION or ULTRA HIGH CONVICTION signals.
- Expected win rate: 58–63%

**State 3: Low-Vol Chop (Stand Aside)**
- Characteristics: VIX < 15 but Nifty going sideways, A/D ratio near 1.0, price oscillating around 50 EMA
- Action: SUPPRESS ALL MOMENTUM SIGNALS. This is the regime that destroys trend-following systems. Either stand aside entirely or switch to mean-reversion logic only. Do NOT run momentum models in this state.
- Expected win rate if you trade momentum here: ~40% (negative expectancy after costs)

**State 4: Crisis/Crash Regime (Survival Mode)**
- Characteristics: VIX > 25 (especially VIX > 30), Nifty below 200 EMA, A/D ratio < 0.8, large gap-downs
- Action: ALL BUY SIGNALS ARE VETOED. Only short signals or cash. Reduce universe to Nifty 50 most liquid stocks only. If already in positions, tighten stops to 1× ATR.
- Exception: VIX > 35 with rapid spike = potential exhaustion signal (contrarian setup, requires 5/6 model agreement)

**Implementation:**
```python
from hmmlearn import hmm
import numpy as np

# Feature matrix: [daily_return, 20d_realized_vol, vix, ad_ratio, dist_from_200ema]
model = hmm.GaussianHMM(n_components=4, covariance_type="full", n_iter=1000)
model.fit(feature_matrix)  # Train on minimum 5 years of Nifty data

# Daily regime prediction
current_regime = model.predict(today_features)
# Regime labels must be assigned by inspecting learned state means
# (State with lowest vol mean = State 1, highest vol mean = State 4)
```

### 3.2 F&O Expiry Cycle Detector
NSE has weekly Nifty/BankNifty expiry (Thursday) and monthly stock expiry (last Thursday of month).

**Rules:**
- Last 3 days before monthly expiry: Max Pain gravity is strongest. For Nifty-correlated stocks, bias predictions toward Max Pain strike direction. Reduce stop-loss distances (price is being "pinned").
- Day after expiry: Sharp moves often occur as hedges are lifted. Widen expected range by 1.5× on expiry+1 day.
- First 2 days of new expiry cycle: Highest reliability for fresh trend signals as new positions are being built.

Build a `days_to_expiry` variable that feeds into both position sizing and range prediction.

### 3.3 VIX Term Structure Analysis
India VIX measures near-term expected volatility. Analyze:
- **VIX Contango (normal):** Near-term VIX < Long-term implied vol → complacency → momentum works well
- **VIX Backwardation (fear):** Near-term VIX > Long-term → stress → momentum works poorly, risk of spike
- **VIX Spike Rate:** If VIX has risen > 20% in 5 days → regime transition likely → reduce all positions by 40%
- **VIX Mean Reversion Signal:** VIX > 30 AND declining from peak → begin scaling back into longs (market recovering)

---

## LAYER 4 — ML DECISION ENGINE

### 4.1 Phase 1: XGBoost/LightGBM Classifier (Deploy Immediately)

**Training Data Construction:**
- Features (X): All 6 model scores, regime state, VIX level, FII flow direction, delivery %, PCR, days to expiry, sector RS score, promoter pledging flag, pre-market gap direction, RVOL
- Labels (y): `1` if stock returned > +2% in next 5 trading days, `0` if returned between -2% and +2%, `-1` if returned < -2%
- Minimum training data: 3 years of daily data across at least 200 stocks = 600,000+ rows

**Walk-Forward Validation (MANDATORY — Non-negotiable):**
```python
# NEVER do random train/test split on financial data — it causes look-ahead bias
# Use time-series cross-validation only:

from sklearn.model_selection import TimeSeriesSplit

tscv = TimeSeriesSplit(n_splits=10, gap=5)  # 5-day gap to prevent leakage

for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    
    model = lgb.LGBMClassifier(
        n_estimators=1000,
        learning_rate=0.02,
        max_depth=6,
        min_child_samples=50,      # Prevents overfitting
        subsample=0.8,
        colsample_bytree=0.7,
        class_weight='balanced',   # Handle imbalanced classes
        random_state=42
    )
    model.fit(X_train, y_train, 
              eval_set=[(X_test, y_test)],
              callbacks=[lgb.early_stopping(50)])
    
    # Store per-fold accuracy — high variance across folds = overfit
    fold_accuracy = accuracy_score(y_test, model.predict(X_test))
```

**Feature Importance Analysis:**
- After training, use SHAP (SHapley Additive exPlanations) to understand which features drive each prediction
- `shap.summary_plot(shap_values, X_test)` → know exactly WHY the model makes each decision
- Any feature with near-zero SHAP importance across all folds → remove it (likely noise)
- Any single feature with >40% of total SHAP importance → investigate for look-ahead bias

**Hyperparameter Optimization:**
- Use Optuna (Bayesian optimization) rather than GridSearch — far more efficient
- Optimize for: Precision on BUY signals (minimize false positives) rather than overall accuracy

### 4.2 Phase 2: Reinforcement Learning Agent (Ultimate Ceiling)

This is the system that never stops learning. It adapts to market regime changes that would kill a static model.

**Framework:** Use Stable-Baselines3 with PPO (Proximal Policy Optimization) or SAC (Soft Actor-Critic)

**Environment Design:**
```python
import gym
from stable_baselines3 import PPO

class AgentAlphaEnv(gym.Env):
    def __init__(self, data, signals):
        # State space: all 6 model scores + regime + macro features
        self.observation_space = gym.spaces.Box(
            low=-np.inf, high=np.inf, 
            shape=(len(feature_names),), dtype=np.float32
        )
        # Action space: 0=HOLD, 1=BUY, 2=SELL, 3=STRONG_BUY (2× size), 4=STRONG_SELL
        self.action_space = gym.spaces.Discrete(5)
    
    def step(self, action):
        # Execute action
        # Calculate reward = actual P&L of the action over next N days
        # CRITICAL: reward must be risk-adjusted (Sharpe-like), not raw return
        # Penalize for drawdowns, not just losses
        reward = self._calculate_risk_adjusted_reward(action)
        return next_state, reward, done, info
    
    def _calculate_risk_adjusted_reward(self, action):
        raw_return = self._get_actual_return()
        drawdown_penalty = max(0, self.current_drawdown - 0.05) * 3  # Penalize >5% DD
        transaction_cost = abs(action != HOLD) * 0.002  # 0.2% round-trip cost
        return raw_return - drawdown_penalty - transaction_cost
```

**Training Protocol:**
- Train on minimum 10 years of historical data
- Use `VecEnv` to train on multiple stocks simultaneously (parallelizes learning)
- Retrain monthly on rolling window — the model never goes stale
- Evaluate on 1-year out-of-sample period before deployment

---

## LAYER 5 — RISK & EXECUTION

### 5.1 Kelly Criterion Position Sizing

The Kelly formula determines optimal bet size to maximize long-run growth:
```
f* = (p × b - q) / b

Where:
f* = fraction of portfolio to risk
p = probability of winning (your model's win rate in current regime)
q = probability of losing = 1 - p
b = net odds (average win / average loss ratio from historical trades)
```

**Implementation:**
- Calculate p and b separately for each regime state using last 252 trading days
- Use **half-Kelly** (f*/2) as the actual sizing — full Kelly is mathematically optimal but psychologically and practically brutal in drawdowns
- Cap maximum single position at 10% of portfolio regardless of Kelly output
- For ULTRA HIGH CONVICTION signals (5/6 model agreement in State 1 regime): allow up to 1.5× half-Kelly, capped at 15%
- For MODERATE BUY signals: use 0.5× half-Kelly
- If current portfolio drawdown > 15% from peak: reduce ALL position sizes to 0.3× half-Kelly (capital preservation mode)

### 5.2 Impact Cost Filter (Execution Reality)
This is where paper trading P&L diverges from real P&L. Model it correctly:

- NSE publishes impact cost for each stock based on ₹1 lakh, ₹5 lakh, and ₹10 lakh order sizes
- For each signal, calculate: `execution_cost = impact_cost + brokerage + STT + exchange_fees + SEBI_charges`
  - Typical round-trip total cost for NSE equity: 0.3–0.5% for large caps, 0.8–2%+ for small caps
- **The edge filter:** Only execute a signal if `expected_edge > 2 × execution_cost`
  - If model predicts +1.5% gain but execution cost is 1.0% round-trip → DO NOT TRADE (only 0.5% net edge)
  - This filter alone eliminates 20–30% of signals but dramatically improves net P&L
- Sort stocks by `net_expected_edge = predicted_return - 2×execution_cost` — highest net edge gets allocated first

### 5.3 Stop Loss Framework
- **Primary Stop:** 1.5× ATR below entry for BUY, 1.5× ATR above for SELL (existing logic — keep)
- **Regime-Adjusted Stop:** Multiply ATR multiplier by regime factor: State 1 = 1.5×, State 2 = 2.0×, State 3 = 2.5×, State 4 = 1.0× (tighter)
- **Trailing Stop:** Once position is +1 ATR in profit, move stop to breakeven. Once +2 ATR, trail stop at -1 ATR from high.
- **Time Stop:** If position has not moved > 1% in either direction within 5 trading days → exit regardless. Dead money is opportunity cost.

### 5.4 Hard Veto System
These rules CANNOT be overridden by any technical or ML signal. They are absolute:

**BLOCK ALL BUY SIGNALS when:**
1. Promoter pledging > 40% AND increasing QoQ
2. Earnings announcement within 3 trading days
3. FII net selling > ₹5000Cr on previous day
4. Stock has hit lower circuit in past 10 days
5. Stock has regulatory/SEBI investigation flag
6. Pre-market SGX Nifty gap down > 1.5%
7. HMM Regime = State 4 (Crisis)
8. VIX has risen > 30% in past 5 trading days

**AUTOMATICALLY EXIT ALL POSITIONS when:**
1. Portfolio drawdown hits 20% from peak (liquidate to cash, wait for State 1 regime)
2. VIX spikes above 40 (systemic crisis event — go to 100% cash)
3. Market-wide circuit breaker triggered (halt trading for remainder of day)

### 5.5 Gap Risk Shield
Since Agent Alpha uses EOD data, it is blind to overnight news. Mitigate with:
- **Pre-market check at 8:00 AM IST:** Run the pre-market regime score (from Layer 1.6) before market open
- If pre-market gap > +2% on a held long position: set limit sell above gap to lock in gains
- If pre-market gap > -2% on a held long position: decide before open whether to exit at open or hold
- **Earnings Blackout:** 5 days before any earnings announcement, reduce position to 50%. Exit completely 1 day before earnings. Re-enter based on fresh signals 2 days after earnings (let the dust settle).
- **SEBI Announcement Monitor:** Any SEBI circular affecting sectors should trigger an immediate review of all positions in that sector.

---

## LAYER 6 — CONTINUOUS IMPROVEMENT

This layer ensures the system never decays. The market evolves; the system must evolve with it.

### 6.1 Alpha Decay Monitor
Every signal's edge has a half-life. This monitor detects when edges are dying:

```python
class AlphaDecayMonitor:
    def __init__(self, signal_names, lookback=60):
        self.signal_names = signal_names
        self.lookback = lookback  # 60-day rolling window
        self.baseline_accuracy = {}  # Set during initial backtest
        self.rolling_accuracy = {}
        self.decay_threshold = 0.08  # 8% absolute drop triggers warning
        
    def update(self, signal_name, prediction, actual_outcome):
        # Update rolling 60-day accuracy for this signal
        self.rolling_accuracy[signal_name].append(
            1 if prediction == actual_outcome else 0
        )
        
        # Check for decay
        current_acc = np.mean(self.rolling_accuracy[signal_name][-self.lookback:])
        baseline_acc = self.baseline_accuracy[signal_name]
        
        if baseline_acc - current_acc > self.decay_threshold:
            # Signal accuracy has dropped by > 8% absolute → decay detected
            self._downweight_signal(signal_name, severity=(baseline_acc - current_acc))
            
    def _downweight_signal(self, signal_name, severity):
        # Reduce this signal's ensemble weight proportionally to decay severity
        # If severity > 15% absolute drop → suspend signal entirely pending review
        if severity > 0.15:
            self.signal_weights[signal_name] = 0  # Suspended
            alert(f"SIGNAL SUSPENDED: {signal_name} has decayed {severity:.1%} below baseline")
        else:
            reduction = severity / 0.15  # Proportional reduction
            self.signal_weights[signal_name] *= (1 - reduction)
```

### 6.2 Walk-Forward Continuous Validation Pipeline
- Every Sunday: Re-run the previous week's predictions against actual outcomes. Calculate:
  - Directional accuracy per model
  - Range prediction accuracy (% of actual closes within predicted High/Low)
  - Hit rate by regime state
  - Hit rate by sector
  - Hit rate by market cap (large cap vs mid cap vs small cap)
- Store all results in a performance database. Build dashboards (see Layer 6.4).
- If any model's 30-day rolling accuracy drops 2 standard deviations below its historical mean → trigger retraining alert.

### 6.3 Automated Model Retraining Schedule
- **XGBoost/LightGBM:** Retrain monthly on rolling 3-year window. Deploy only if new model beats current model in out-of-sample test.
- **HMM Regime Classifier:** Retrain quarterly (regimes shift slowly). Validate that 4 states are still meaningfully distinct.
- **RL Agent:** Retrain monthly on rolling window. Evaluate on past 3 months before replacing production model.
- **Feature Engineering Review:** Quarterly, review SHAP values. Features whose importance has dropped to near-zero should be reviewed for removal (market may have arbitraged them away).
- **Signal Correlation Monitor:** If two models start generating highly correlated signals (Pearson r > 0.85), they are no longer independent and the ensemble loses diversification value. Investigate and differentiate.

### 6.4 Performance Attribution Dashboard
Build a live dashboard that shows:
- Overall system performance: Total return, Sharpe ratio, Sortino ratio, Max drawdown
- Performance by regime state (which regime is the system best/worst in)
- Performance by model (which of the 6 models is contributing most/least alpha)
- Performance by sector (which sectors is the system best at predicting)
- Prediction vs Actual table with yesterday's predicted High/Low vs actual High/Low (existing feature — keep)
- Alpha decay curves: Rolling 60-day accuracy trend line per signal

---

## ADDITIONAL ADVANCED UPGRADES (IMPLEMENT AFTER CORE LAYERS)

### A: Kalman Filter for Dynamic Signal Weighting
Instead of fixed model weights in the ensemble, use a Kalman filter to dynamically estimate the "true" weight of each model based on its recent performance. Models that are performing well in the current regime receive higher weight automatically. Models that are underperforming have their weight reduced. This makes the ensemble self-optimizing.

```python
from pykalman import KalmanFilter

# State vector = [model_1_weight, model_2_weight, ..., model_6_weight]
# Observation = actual signal accuracy per model per day
# The filter maintains a running estimate of each model's current effectiveness
kf = KalmanFilter(n_dim_obs=6, n_dim_state=6)
weights_estimate, _ = kf.filter(daily_accuracy_matrix)
current_weights = weights_estimate[-1]  # Use latest weight estimate
```

### B: Sector Rotation Intelligence
Build a sector rotation model:
- Calculate rolling 1-month, 3-month, 6-month returns for each NSE sector index
- Identify which sectors are in leadership (top 3 momentum) vs laggard (bottom 3)
- **Boost** scores for stocks in leading sectors by +5
- **Penalize** scores for stocks in lagging sectors by -5
- Track sector rotation sequence: typically Financials lead early cycle, IT and Pharma lead late cycle, Energy and Materials peak mid-cycle. Identify current cycle position.

### C: Pairs Trading / Statistical Arbitrage Layer
Identify highly cointegrated stock pairs (e.g., HDFC Bank vs ICICI Bank, TCS vs Infosys):
- Run Engle-Granger cointegration test on all stock pairs in the same sector
- For cointegrated pairs with p-value < 0.05: build a spread Z-score
- `z_score = (spread - spread_mean) / spread_std`
- Z-score > +2 → long the laggard, short the leader (convergence trade)
- Z-score < -2 → reverse
- This is a market-neutral strategy that generates alpha independent of market direction — extremely valuable during State 3 (Chop) regime when directional signals are suppressed

### D: Alternative Data Integration (Phase 3 — Advanced)
These require external data subscriptions but represent the frontier of edge:
- **Satellite foot traffic data for retail stocks:** Correlates with quarterly revenue
- **App download/usage metrics** (via Sensor Tower or Apptopia) for consumer tech stocks
- **Google Trends** for brand popularity of consumer companies (free, surprisingly predictive)
- **LinkedIn job posting growth rate** for tech companies (hiring surge = growth signal)
- **Patent filing rate** for pharma/technology stocks (R&D pipeline signal)

---

## TECHNICAL IMPLEMENTATION REQUIREMENTS

### Database Architecture
- Use **TimescaleDB** (PostgreSQL extension optimized for time-series) for all price and signal data
- Separate tables for: raw prices, adjusted prices, signals, regime states, ML predictions, actual outcomes, performance attribution
- Partition tables by year for query performance
- Daily backup to cloud storage

### API Design
- Build a RESTful API layer on top of the analysis engine
- Endpoints:
  - `GET /signals/today` → today's complete signal output for all stocks
  - `GET /regime/current` → current regime state with confidence
  - `GET /performance/rolling` → rolling 30/60/90 day performance metrics
  - `GET /stock/{symbol}/analysis` → complete analysis for single stock
  - `POST /backtest` → run backtest with custom parameters

### Data Pipeline Scheduling (use Apache Airflow or simple cron)
```
06:00 IST  → Pull pre-market data (SGX, Dow futures, USD/INR, Crude)
08:00 IST  → Calculate pre-market regime score, flag gap risk
09:15 IST  → Market open — begin intraday monitoring (OFI calculation)
15:35 IST  → Pull final EOD data after market close
16:00 IST  → Pull FII/DII data (published after market close)
16:30 IST  → Pull delivery percentage data (published ~1 hr after close)
17:00 IST  → Run all 6 signal models on fresh EOD data
17:30 IST  → Run ML ensemble, calculate final scores and signals
18:00 IST  → Generate report, update dashboard, send alerts
19:00 IST  → Run alpha decay check and performance attribution
Sunday 20:00 → Weekly model validation and retraining trigger
```

### Code Quality Requirements
- Every function must have a docstring explaining: what it calculates, mathematical formula used, expected input/output types
- Every signal calculation must have unit tests with known input/output pairs
- Use type hints throughout (`def calculate_ofi(tick_data: pd.DataFrame) -> float:`)
- Logging at INFO level for all signal calculations, DEBUG for intermediate steps, ERROR for any data quality issues
- If any input data is missing or stale → log the issue and fall back gracefully (use last known value with a staleness flag, never crash)

---

## OUTPUT FORMAT REQUIREMENTS

### Per-Stock Signal Output (upgrade existing output)
For each stock in the universe, produce:

```json
{
  "symbol": "RELIANCE",
  "date": "2026-01-15",
  "signal": "HIGH CONVICTION BUY",
  "ensemble_score": 76,
  "model_votes": {
    "momentum": {"signal": "BUY", "confidence": 72},
    "order_flow": {"signal": "BUY", "confidence": 81},
    "options": {"signal": "NEUTRAL", "confidence": 45},
    "sentiment": {"signal": "BUY", "confidence": 68},
    "fii_dii": {"signal": "BUY", "confidence": 85},
    "volume": {"signal": "BUY", "confidence": 74}
  },
  "regime_state": 1,
  "regime_label": "Low-vol uptrend",
  "hard_vetoes_active": [],
  "predicted_range": {
    "method": "options_implied",
    "predicted_high": 1342.50,
    "predicted_low": 1298.75,
    "confidence": "78%"
  },
  "risk_metrics": {
    "entry_price": 1318.40,
    "stop_loss": 1285.20,
    "target_1": 1355.00,
    "target_2": 1390.00,
    "risk_reward_ratio": 2.8,
    "kelly_fraction": 0.043,
    "impact_cost_pct": 0.12,
    "net_expected_edge": 2.76
  },
  "flags": {
    "earnings_blackout": false,
    "promoter_pledging_alert": false,
    "delivery_pct": 68.4,
    "bulk_deal_last_5d": true,
    "fii_consecutive_buying_days": 7
  },
  "ml_probability": {
    "strong_buy": 0.42,
    "buy": 0.31,
    "neutral": 0.18,
    "sell": 0.09
  },
  "alpha_decay_status": {
    "all_signals_healthy": true,
    "weakest_signal": "options",
    "weakest_signal_rolling_accuracy": "61%"
  }
}
```

---

## PERFORMANCE BENCHMARKS — HOW TO KNOW YOU'VE SUCCEEDED

After full implementation, the system should achieve the following in out-of-sample backtesting (never in-sample):

| Metric | Minimum Target | Elite Target |
|--------|---------------|-------------|
| Directional Win Rate (State 1) | 65% | 72% |
| Directional Win Rate (All Regimes) | 58% | 65% |
| Range Prediction Accuracy | 75% | 82% |
| Sharpe Ratio (annualized) | > 1.5 | > 2.5 |
| Sortino Ratio | > 2.0 | > 3.5 |
| Maximum Drawdown | < 20% | < 12% |
| Win/Loss Ratio | > 1.8 | > 2.5 |
| Profit Factor | > 1.5 | > 2.2 |

If backtested results look dramatically better than these (e.g., 95% win rate), you have a look-ahead bias in your backtest. Investigate immediately — common causes are: using closing price for entry (must use next day open), using quarterly data available only after the quarter ends, or training/testing on overlapping periods.

---

## FINAL CRITICAL INSTRUCTIONS

1. **Never hard-code any threshold.** Every parameter (ATR multiplier, Kelly fraction, regime thresholds, signal weights) must be configurable via a central `config.yaml` file.

2. **Build the monitoring dashboard FIRST.** Before you have perfect signals, you need to see what's happening. The dashboard is how you debug and improve everything else.

3. **Paper trade for minimum 3 months before deploying real capital.** Compare live predictions vs actual outcomes daily. The gap between backtest and live will reveal hidden bugs.

4. **The regime classifier is the master controller.** Every other component should query the current regime state before acting. Build it first, test it thoroughly, trust it completely.

5. **Document every data source, every formula, every assumption.** Six months from now, you need to be able to explain why any particular trade was taken. This is also required for SEBI compliance as a systematic trading participant.

6. **Expect the first 6 months of real trading to underperform the backtest.** This is universal. The gap narrows as the RL agent accumulates live experience and the alpha decay monitor calibrates signal weights to current market conditions.

---

*Agent Alpha v2.0 — Built to the maximum accuracy ceiling achievable in systematic trading. Not 99%. But elite. And honest about it.*
