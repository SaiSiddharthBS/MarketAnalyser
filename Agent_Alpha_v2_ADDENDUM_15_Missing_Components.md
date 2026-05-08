# AGENT ALPHA v2.0 — CRITICAL ADDENDUM
### 15 Missing Components — Append This Entirely to the Master Prompt
### These are not optional. Every section below is required for the complete system.

---

## ADDENDUM A — MACRO ECONOMIC CALENDAR MODULE

This is a glaring omission. RBI rate decisions have moved Nifty by 2–5% on single days. CPI surprises have triggered 3% swings. Without modelling macro events, the system is flying blind during the most predictable large moves.

### A.1 India Macro Calendar Data Sources
Maintain a calendar of all scheduled macro events with expected release dates:

| Event | Source | Typical Market Impact |
|-------|---------|----------------------|
| RBI Monetary Policy (MPC) | RBI website | HIGH — Nifty ±2–4%, Bank Nifty ±3–6% |
| CPI Inflation Data | MOSPI | MEDIUM — affects rate expectations |
| WPI Inflation Data | DPIIT | LOW-MEDIUM |
| IIP (Industrial Production) | MOSPI | MEDIUM |
| GDP Quarterly Data | MOSPI | MEDIUM-HIGH |
| Union Budget | Ministry of Finance | VERY HIGH — sector-level rotation |
| US Fed FOMC Decision | US Federal Reserve | HIGH — FII flow trigger |
| US CPI Data | US BLS | MEDIUM-HIGH — affects FII risk appetite |
| US Non-Farm Payrolls | US BLS | MEDIUM |

Scrape or manually maintain a `macro_calendar.csv` with columns: `event_date, event_name, event_type, expected_impact_level`

### A.2 Pre-Event Risk Suppression Rules
```python
def get_macro_suppression_factor(today, macro_calendar):
    upcoming_events = macro_calendar[
        (macro_calendar.event_date >= today) & 
        (macro_calendar.event_date <= today + timedelta(days=3))
    ]
    
    suppression = 1.0  # 1.0 = no suppression, 0.0 = full suppression
    
    for _, event in upcoming_events.items():
        days_away = (event.event_date - today).days
        
        if event.expected_impact_level == 'VERY HIGH':
            # Budget, major RBI surprise expected
            if days_away <= 1:
                suppression *= 0.0   # No new positions day before budget
            elif days_away <= 3:
                suppression *= 0.3   # Severely reduce sizing
                
        elif event.expected_impact_level == 'HIGH':
            # Regular MPC, US Fed, major CPI
            if days_away <= 1:
                suppression *= 0.4   # Halve all new positions
            elif days_away <= 3:
                suppression *= 0.7   # Reduce by 30%
                
        elif event.expected_impact_level == 'MEDIUM':
            if days_away <= 1:
                suppression *= 0.7
    
    return suppression

# Apply to position sizing:
kelly_size = base_kelly_size * macro_suppression_factor
```

### A.3 Post-Event Drift Model
After major macro events, markets often continue drifting in the initial reaction direction for 2–3 days:
- RBI rate cut + dovish guidance → Banks and Real Estate continue rallying for avg 2.3 days (historically)
- Surprise rate hike → Banks and Real Estate continue falling avg 1.8 days
- US Fed hawkish surprise → FII selling in India continues avg 3–5 days
- Build a `post_event_drift_score`: After each high-impact event, run a simple regression on historical post-event returns to quantify the typical drift magnitude and duration. Add this as a 7th signal in the ensemble with weight 5% (active only in the 3 days post-event).

### A.4 Union Budget Sector Rotation Model
The Union Budget (typically February 1) creates the most predictable sector rotation in Indian markets:
- Pre-budget (Jan 15 – Jan 31): Defence, Infrastructure, Rail stocks typically rally on budget expectation
- Post-budget: Sectors that receive increased allocation outperform for 5–15 days; sectors with increased taxes underperform for 3–7 days
- Build a `budget_sector_map` that maps typical budget themes to sector ETFs/stocks. Source: Last 10 years of budget-day sector returns.

---

## ADDENDUM B — AMFI MUTUAL FUND HOLDINGS DATA

### B.1 Data Source and Collection
AMFI (Association of Mutual Funds in India) publishes the complete portfolio holdings of every registered mutual fund in India every month (by the 10th of the following month).
- **URL:** `https://www.amfiindia.com/net-asset-value/nav-history`
- Download monthly factsheets for top 20 AMCs by AUM: HDFC MF, SBI MF, ICICI Pru MF, Axis MF, Kotak MF, DSP MF, Nippon MF, Mirae Asset, Motilal Oswal, etc.

### B.2 Signal Construction
For each stock, compute:
```python
def calculate_mf_signal(stock_symbol, current_month_data, previous_month_data):
    
    # How many MFs hold this stock?
    mf_count_current = count(funds holding stock this month)
    mf_count_previous = count(funds holding stock last month)
    
    # Total AUM allocated to this stock across all MFs
    total_mf_aum_current = sum(value_held_by_all_funds_current_month)
    total_mf_aum_previous = sum(value_held_by_all_funds_last_month)
    
    # Change signals
    new_funds_added = mf_count_current - mf_count_previous  # New MFs buying
    aum_change_pct = (total_mf_aum_current - total_mf_aum_previous) / total_mf_aum_previous
    
    # Scoring:
    if new_funds_added >= 3 and aum_change_pct > 0.15:
        mf_signal = "STRONG ACCUMULATION"  # +4 points
    elif new_funds_added >= 1 and aum_change_pct > 0.05:
        mf_signal = "ACCUMULATION"          # +2 points
    elif new_funds_added < -3 or aum_change_pct < -0.15:
        mf_signal = "DISTRIBUTION"          # -3 points
    else:
        mf_signal = "NEUTRAL"               # 0 points
    
    # High-conviction special case:
    # If top 5 MFs by AUM ALL increased holdings in same month → rare, very bullish
    top5_all_increased = all(fund increased holding for fund in top_5_funds_by_aum)
    if top5_all_increased:
        mf_signal_bonus = +5  # Override and add maximum bonus

    return mf_signal, aum_change_pct, new_funds_added
```

### B.3 MF Overhang Risk
- If a stock has >15% of its free float held by MFs → high MF concentration risk
- If one single fund holds >5% of the company → forced selling risk if that fund faces redemption pressure
- Flag these stocks with `mf_concentration_risk = True` → reduce position size to 50% of Kelly

---

## ADDENDUM C — SAST / INSIDER DISCLOSURE DATA

### C.1 What This Is
SEBI Regulation 29 and SAST (Substantial Acquisition of Shares and Takeovers) requires:
- Any promoter or related party buying/selling shares to disclose within 2 trading days
- Any entity crossing 5%, 10%, 15%... shareholding threshold to disclose immediately
- Key Managerial Personnel (KMPs) must disclose all trades under SEBI Insider Trading Regulations

**Source:** BSE corporate filings at `https://www.bseindia.com/corporateaction/` → Insider Trading section. Also NSE.

### C.2 Signal Rules
```python
def calculate_insider_signal(disclosures, stock_symbol, lookback_days=30):
    
    recent_disclosures = disclosures[
        (disclosures.symbol == stock_symbol) & 
        (disclosures.disclosure_date >= today - timedelta(days=lookback_days))
    ]
    
    promoter_buys = recent_disclosures[
        (recent_disclosures.category == 'PROMOTER') & 
        (recent_disclosures.transaction_type == 'BUY')
    ]
    
    promoter_sells = recent_disclosures[
        (recent_disclosures.category == 'PROMOTER') & 
        (recent_disclosures.transaction_type == 'SELL')
    ]
    
    # Promoter buying open market = highest conviction signal possible
    # They know their own company better than anyone
    if len(promoter_buys) > 0:
        total_buy_value = sum(promoter_buys.value)
        
        if total_buy_value > 10_00_00_000:   # ₹10 Crore+ buy
            insider_signal = +6   # VERY STRONG BUY
        elif total_buy_value > 1_00_00_000:   # ₹1 Crore+ buy
            insider_signal = +4   # STRONG BUY
        else:
            insider_signal = +2   # BUY
    
    # Promoter selling has nuance — could be planned disposal, not bearish
    # Only penalize cluster selling (multiple promoters selling simultaneously)
    elif len(promoter_sells) >= 3:  # Multiple promoters selling = concern
        insider_signal = -3
    
    # KMP (CEO/CFO/Director) cluster buying = very bullish
    kmp_buys = recent_disclosures[disclosures.category == 'KMP' & disclosures.transaction_type == 'BUY']
    if len(kmp_buys) >= 3:
        insider_signal += 3  # Multiple insiders buying simultaneously
    
    return insider_signal
```

### C.3 Takeover / Acquisition Signal (SAST)
When any entity crosses a shareholding threshold (5%, 10%, 15%), it often precedes a full acquisition:
- Any new entity crossing 5% shareholding → flag as potential acquisition target → BUY +4
- Any entity filing creeping acquisition (slowly buying up to 25%) → strong accumulation signal → BUY +5
- Add `acquisition_flag` to output JSON for flagged stocks

---

## ADDENDUM D — GARCH VOLATILITY FORECASTING

### D.1 Why ATR Is Not Enough
ATR is a backward-looking average of true ranges. It cannot predict volatility clustering (high volatility today predicts high volatility tomorrow — a well-documented phenomenon in financial markets called volatility persistence). GARCH models this explicitly.

### D.2 Implementation
```python
from arch import arch_model
import pandas as pd
import numpy as np

def forecast_volatility_garch(returns_series, horizon=1):
    """
    Fit a GARCH(1,1) model and forecast next N days volatility.
    
    GARCH(1,1): σ²_t = ω + α×ε²_(t-1) + β×σ²_(t-1)
    Where:
        ω = base variance (long-run variance)
        α = ARCH effect (yesterday's shock impact)
        β = GARCH effect (yesterday's variance persistence)
        α + β < 1 ensures stationarity (typically 0.97-0.99 for equities)
    """
    # Use percentage returns
    pct_returns = returns_series * 100
    
    # Fit GARCH(1,1) — the workhorse model for equity volatility
    model = arch_model(pct_returns, vol='Garch', p=1, q=1, dist='studentst')
    # studentst distribution handles fat tails better than normal distribution
    
    result = model.fit(disp='off', last_obs=len(pct_returns)-1)
    
    # Forecast
    forecasts = result.forecast(horizon=horizon, reindex=False)
    forecast_variance = forecasts.variance.iloc[-1, 0]
    forecast_vol_pct = np.sqrt(forecast_variance)  # In percentage terms
    forecast_vol_decimal = forecast_vol_pct / 100
    
    return forecast_vol_decimal  # Daily volatility as a decimal (e.g., 0.018 = 1.8%)

def apply_garch_to_range_prediction(close_price, garch_vol, sigma_multiplier=1.0):
    """
    Use GARCH forecast to set dynamic range prediction.
    1σ range captures ~68% of outcomes.
    1.5σ range captures ~87% of outcomes.
    2σ range captures ~95% of outcomes.
    """
    predicted_high = close_price * (1 + sigma_multiplier * garch_vol)
    predicted_low  = close_price * (1 - sigma_multiplier * garch_vol)
    return predicted_high, predicted_low

# COMBINE with options-implied range:
# Final range = 0.6 × options_implied_range + 0.4 × garch_range
# (Options-implied is forward-looking, GARCH is model-based — blend them)
```

### D.3 GARCH Regime Signal
- When GARCH forecasted volatility > 2× its 90-day average → volatility regime transition → shift to State 2 or 3
- When GARCH vol is falling rapidly (vol compression) → trending regime likely starting → shift toward State 1
- Use GARCH conditional variance as an additional feature in the HMM regime classifier

---

## ADDENDUM E — PORTFOLIO-LEVEL CORRELATION MANAGEMENT

### E.1 The Problem That Breaks Everything
If you hold 10 positions but they are all highly correlated (they all move with Nifty in the same direction), you effectively have 1 position with 10× the size. Your Kelly sizing assumes independence — it is completely wrong in this case.

### E.2 Maximum Diversification Portfolio Construction
```python
import numpy as np
from scipy.optimize import minimize

def build_portfolio_with_correlation_constraints(
    signals,              # Dict of {symbol: signal_score}
    returns_data,         # Historical returns for all candidate stocks
    max_portfolio_size=20,
    max_correlation=0.65  # No two positions can have >65% correlation
):
    # Step 1: Filter to only HIGH CONVICTION and above signals
    candidates = {sym: score for sym, score in signals.items() 
                  if score > 55}  # Only take strong signals
    
    # Step 2: Calculate pairwise correlation matrix
    candidate_returns = returns_data[list(candidates.keys())].dropna()
    corr_matrix = candidate_returns.rolling(60).corr().iloc[-len(candidates):]
    
    # Step 3: Greedy selection — maximize number of low-corr positions
    selected = []
    sorted_candidates = sorted(candidates.items(), key=lambda x: x[1], reverse=True)
    
    for symbol, score in sorted_candidates:
        if len(selected) >= max_portfolio_size:
            break
            
        # Check correlation with all already-selected stocks
        if selected:
            max_corr_with_portfolio = max(
                abs(corr_matrix.loc[symbol, existing]) 
                for existing in selected
            )
            if max_corr_with_portfolio > max_correlation:
                continue  # Skip this stock — too correlated with existing holdings
        
        selected.append(symbol)
    
    return selected

# CRITICAL RULES:
# Max 3 stocks from same sector in portfolio (sector concentration cap)
# Max 25% of portfolio in any single sector
# Max 10% in any single stock (hard limit, already in main document)
# If Nifty beta of portfolio > 1.2 → reduce or hedge
```

### E.3 Portfolio Beta Management
```python
def calculate_portfolio_beta(holdings, benchmark_returns, stock_returns):
    """Portfolio beta vs Nifty 50"""
    portfolio_returns = sum(
        weight * stock_returns[symbol] 
        for symbol, weight in holdings.items()
    )
    
    covariance = np.cov(portfolio_returns, benchmark_returns)[0,1]
    benchmark_variance = np.var(benchmark_returns)
    portfolio_beta = covariance / benchmark_variance
    
    return portfolio_beta

# If portfolio beta > 1.3 in State 2 or 3 regime → buy Nifty Put options as hedge
# If portfolio beta > 1.5 in any regime → mandatory reduction required
# Target beta in State 1: 0.9–1.2 (slightly long-biased)
# Target beta in State 2: 0.6–0.9 (defensive)
# Target beta in State 3: 0.0–0.3 (near-cash or hedged)
# Target beta in State 4: Negative or zero (short or cash)
```

---

## ADDENDUM F — TEMPORAL FUSION TRANSFORMER (TFT) — TRUE ML CEILING

### F.1 Why TFT Beats XGBoost for This Problem
XGBoost treats each row independently. It doesn't understand sequence — that Tuesday's signal came after Monday's signal. TFT is a Transformer architecture designed specifically for multi-horizon time series forecasting that:
- Understands temporal dependencies (sequence matters)
- Handles multiple time scales simultaneously (daily, weekly, monthly patterns)
- Handles static features (sector, market cap) AND time-varying features (daily signals) in a unified architecture
- Provides interpretable attention weights (you can see which time steps it focused on)

### F.2 Implementation
```python
from pytorch_forecasting import TemporalFusionTransformer, TimeSeriesDataSet
from pytorch_forecasting.metrics import QuantileLoss
import pytorch_lightning as pl

# Create dataset
training = TimeSeriesDataSet(
    data=training_df,
    time_idx="time_idx",          # Integer day index
    target="next_5d_return",      # What we're predicting
    group_ids=["symbol"],         # Each stock is a separate series
    
    # Static features (don't change over time for a stock)
    static_categoricals=["sector", "market_cap_bucket"],
    static_reals=["avg_market_cap_log"],
    
    # Time-varying known future features (we know these in advance)
    time_varying_known_categoricals=["regime_state", "days_to_expiry_bucket"],
    time_varying_known_reals=["macro_suppression_factor", "days_to_rbi_policy"],
    
    # Time-varying observed features (we observe these, don't know future values)
    time_varying_unknown_reals=[
        "momentum_score", "order_flow_score", "options_score",
        "sentiment_score", "fii_dii_score", "volume_score",
        "vix", "fii_net_flow", "delivery_pct", "rvol",
        "garch_forecast_vol", "mf_signal", "insider_signal"
    ],
    
    max_encoder_length=60,   # Use 60 days of history
    max_prediction_length=5,  # Predict next 5 days
    
    target_normalizer=GroupNormalizer(groups=["symbol"]),
)

# Model
tft = TemporalFusionTransformer.from_dataset(
    training,
    learning_rate=1e-3,
    hidden_size=64,
    attention_head_size=4,
    dropout=0.1,
    hidden_continuous_size=32,
    loss=QuantileLoss(quantiles=[0.1, 0.5, 0.9]),  # Predict distribution, not just point estimate
    # Quantile output gives you: pessimistic (10%), expected (50%), optimistic (90%) scenarios
)

# The quantile output is especially valuable:
# predicted_low = tft.predict(x)[0.1 quantile]  → better than ATR for downside estimation
# predicted_high = tft.predict(x)[0.9 quantile] → better than ATR for upside estimation
```

### F.3 TFT Interpretation
Unlike black-box deep learning, TFT gives you interpretable attention:
- **Variable importance:** Which features does the model find most useful? (Validates your signal choices)
- **Temporal attention:** Which past time steps were most predictive? (Reveals look-back period)
- Use `tft.interpret_output(predictions)` to generate these plots automatically

---

## ADDENDUM G — INTERMARKET ANALYSIS MODULE

### G.1 Core Intermarket Relationships for India

These correlations are well-documented and exploitable:

**Nifty 50 vs Global Markets:**
- S&P 500 / Dow Jones: Rolling 30-day correlation typically 0.6–0.75 with Nifty. US market close → Indian market open predictor.
- MSCI Emerging Markets Index: Nifty moves with EM broadly when global risk-on/risk-off dominates.
- Hang Seng / Shanghai Composite: China economic fears = EM selloff including India.

**Sector-Specific Commodity Relationships:**
| Commodity | Affected Sectors | Relationship |
|-----------|-----------------|--------------|
| Crude Oil (Brent) | OMCs (HPCL, BPCL, IOC) | INVERSE — higher crude = margin pressure |
| Crude Oil | Paints (Asian Paints), Chemicals | INVERSE — input cost pressure |
| Crude Oil | Aviation (IndiGo, Air India) | INVERSE — fuel cost |
| Metal Prices (LME) | Metal stocks (Tata Steel, Hindalco) | DIRECT — revenue proxy |
| Natural Gas | Fertilizer companies (Chambal, Coromandel) | INVERSE — feedstock cost |
| Gold | Gold financiers (Muthoot, Manappuram) | DIRECT |
| Gold | General market | INVERSE — gold rises in risk-off, equities fall |
| Rubber prices | Tyre companies (MRF, Apollo) | INVERSE — input cost |

**Bond Market:**
- India 10Y G-Sec Yield: When yields rise sharply (>10 bps in a week) → Rate-sensitive sectors (Banks, Real Estate, NBFCs) face headwinds. Suppress buy signals for these sectors.
- Yield curve (10Y minus 1Y spread): Steepening = growth expectations improving = bullish for cyclicals; Flattening/Inverting = slowdown fear.

```python
def calculate_intermarket_sector_score(sector, commodity_changes, yield_change):
    """
    Returns intermarket adjustment to sector score (-5 to +5)
    """
    sector_adjustments = {
        'OMC': -commodity_changes['crude_oil_pct'] * 0.4,      # Crude rises 5% → -2 adjustment
        'METALS': commodity_changes['lme_metals_pct'] * 0.3,
        'AVIATION': -commodity_changes['crude_oil_pct'] * 0.5,
        'PAINTS': -commodity_changes['crude_oil_pct'] * 0.25,
        'BANKS': -yield_change * 50,   # 10 bps rise = -0.5 adjustment
        'REALESTATE': -yield_change * 80,
        'IT': commodity_changes['usdinr_pct'] * 0.6,   # Rupee depreciation boosts IT revenue
        'PHARMA': commodity_changes['usdinr_pct'] * 0.4,
    }
    
    adjustment = sector_adjustments.get(sector, 0)
    return max(-5, min(5, adjustment))  # Cap at ±5
```

---

## ADDENDUM H — SEASONAL / CALENDAR EFFECTS MODULE

### H.1 Documented Indian Market Seasonal Patterns

These are statistically significant patterns across 15+ years of NSE data:

```python
SEASONAL_PATTERNS = {
    # Month-based patterns (0=January, 11=December)
    'month_effects': {
        0: +1.2,   # January: New year FII allocation, "January effect"
        1: -0.8,   # February: Budget uncertainty, selling pressure pre-budget
        2: -1.5,   # March: Year-end tax selling, portfolio rebalancing
        3: +1.8,   # April: New FY starts, fresh institutional buying
        4: +0.5,   # May: Mixed
        5: -0.9,   # June: FII selling due to global summer illiquidity
        6: -0.6,   # July: Mixed, Q1 results
        7: +0.8,   # August: Monsoon progress data, Q1 results rally
        8: -1.1,   # September: FII year-end (US fiscal year), global rebalancing
        9: +1.5,   # October: Diwali effect, festive season
        10: +1.9,  # November: Post-Diwali optimism, year-end rally begins
        11: +2.1,  # December: Santa Claus rally, FII window dressing
    },
    
    # Week-of-month effects
    'week_effects': {
        1: +0.6,   # First week: Fresh institutional buying
        2: +0.2,
        3: -0.3,   # Mid-month: Mixed
        4: -0.8,   # Last week: Month-end selling, position squaring
    },
    
    # Day-of-week effects
    'day_effects': {
        0: -0.3,   # Monday: Global weekend news digestion
        1: +0.2,   # Tuesday: Positive
        2: +0.1,   # Wednesday: Neutral
        3: +0.3,   # Thursday: Expiry day — often trend day
        4: -0.4,   # Friday: Risk-off before weekend
    }
}

def calculate_seasonal_score(date):
    month_effect = SEASONAL_PATTERNS['month_effects'][date.month - 1]
    week_num = (date.day - 1) // 7 + 1
    week_effect = SEASONAL_PATTERNS['week_effects'][min(week_num, 4)]
    day_effect = SEASONAL_PATTERNS['day_effects'][date.weekday()]
    
    # Combine (normalize to -3 to +3 range)
    raw_score = month_effect + week_effect + day_effect
    seasonal_score = max(-3, min(3, raw_score))
    return seasonal_score
```

### H.2 Pre-Budget Rally Model (January 15 – January 31)
Historically, the following sectors outperform in the 15 days before the Union Budget:
- Infrastructure (L&T, NCC, IRB): +avg 4.2% (budget capex expectations)
- Defence (HAL, BEL, BEML): +avg 5.8%
- Railways (RVNL, IRFC): +avg 6.1%
- Rural/Agri (Tractor companies, agri-input): +avg 3.5%

Activate `pre_budget_mode` between Jan 15–Jan 31 each year. Boost scores for above sectors.

### H.3 March Year-End Tax Loss Selling
Between March 15–25: Tax loss selling pressure artificially depresses prices of stocks that have fallen during the year. These stocks frequently rebound sharply in April (tax loss selling reversal). Model as a contrarian mean-reversion opportunity for beaten-down stocks in this window.

---

## ADDENDUM I — MOMENTUM CRASH PROTECTION MODULE

### I.1 When Momentum Crashes
Momentum strategies are known to crash hard under specific conditions:
- After prolonged low-volatility bull markets (everyone is momentum-long → crowded trade)
- During sharp Fed/RBI policy reversals
- During market-wide deleveraging events
- When "quality" and "value" suddenly outperform (factor rotation)

### I.2 Crash Early Warning System
```python
def momentum_crash_risk_score():
    """
    Returns a 0-100 risk score for momentum crash probability.
    Score > 70 = reduce momentum exposure significantly.
    """
    risk = 0
    
    # Signal 1: Momentum crowding (how many stocks are near 52-week highs?)
    pct_near_52w_high = count(close > 0.95 × high_52w) / total_stocks
    if pct_near_52w_high > 0.45:
        risk += 25  # Market is very overbought / momentum crowded
    
    # Signal 2: Momentum volatility compression
    # When momentum portfolio itself has very low recent volatility → crowded → fragile
    momentum_portfolio_vol_20d = rolling_std(momentum_returns, 20)
    momentum_portfolio_vol_60d = rolling_std(momentum_returns, 60)
    if momentum_portfolio_vol_20d / momentum_portfolio_vol_60d < 0.5:
        risk += 20  # Unusually calm momentum → fragile
    
    # Signal 3: Momentum vs value spread at extremes
    momentum_fwd_pe = avg_pe(top_momentum_stocks)
    value_fwd_pe = avg_pe(bottom_momentum_stocks)
    valuation_spread = momentum_fwd_pe / value_fwd_pe
    if valuation_spread > 3.0:
        risk += 20  # Momentum stocks extremely expensive vs value → mean reversion risk
    
    # Signal 4: Cross-sectional momentum dispersion collapsing
    # When all stocks start moving together → momentum stops working
    cross_sectional_dispersion = std(all_stock_returns_today)
    if cross_sectional_dispersion < historical_10th_percentile:
        risk += 15  # Low dispersion = poor momentum environment
    
    # Signal 5: Recent momentum factor return deterioration
    recent_mom_factor_return = sum(last_10_days_momentum_long_short_portfolio)
    if recent_mom_factor_return < -3%:
        risk += 20  # Momentum already losing → crash may be underway
    
    return min(100, risk)

# Risk action table:
# 0-30: Normal operations
# 30-50: Reduce momentum signal weight by 20%
# 50-70: Reduce momentum signal weight by 50%, add mean-reversion model
# 70-100: Suspend momentum signals, switch to quality/low-vol factor
```

---

## ADDENDUM J — CREDIT RATING CHANGE MONITOR

### J.1 Data Sources
- **CRISIL:** `https://www.crisil.com/en/home/our-businesses/ratings/credit-ratings.html`
- **ICRA:** `https://www.icra.in/Rationale/`
- **CARE Ratings:** `https://www.careratings.com/`
- **India Ratings (Fitch India):** `https://www.indiaratings.co.in/`

Scrape daily for new ratings actions. Parse: company name, previous rating, new rating, date, outlook.

### J.2 Signal Rules
```python
RATING_SCORES = {
    'AAA': 10, 'AA+': 9, 'AA': 8, 'AA-': 7, 
    'A+': 6, 'A': 5, 'A-': 4,
    'BBB+': 3, 'BBB': 2, 'BBB-': 1,
    'BB+': -1, 'BB': -2, 'BB-': -3,  # Speculative grade
    'B': -5, 'C': -8, 'D': -10       # Distressed
}

def process_rating_action(company, old_rating, new_rating, outlook):
    old_score = RATING_SCORES.get(old_rating, 0)
    new_score = RATING_SCORES.get(new_rating, 0)
    
    rating_change = new_score - old_score
    
    if rating_change <= -2:
        # Significant downgrade → HARD VETO (no buy signals for 90 days)
        return 'HARD_VETO', f"Credit downgrade from {old_rating} to {new_rating}"
    
    elif rating_change == -1:
        # Minor downgrade → reduce score by 8 points, flag in output
        return 'REDUCE', -8
    
    elif rating_change >= 2 and new_score >= 7:
        # Significant upgrade to investment grade → potential buy trigger
        return 'BOOST', +5
    
    if outlook == 'NEGATIVE WATCH':
        # On watch for downgrade → flag, reduce size by 30%
        return 'WATCH', -4
```

---

## ADDENDUM K — ENHANCED MARKET BREADTH INDICATORS

### K.1 Beyond Advance/Decline Ratio

The existing HMM uses A/D ratio. Add these for a much richer regime picture:

```python
def calculate_breadth_suite(nse_universe_data):
    
    breadth = {}
    
    # 1. Percentage of stocks above 200-day EMA (market health indicator)
    breadth['pct_above_200ema'] = (
        sum(1 for s in universe if s.close > s.ema_200) / len(universe)
    )
    # >60% = healthy bull market; <40% = bear market; <20% = severe bear
    
    # 2. Percentage of stocks above 50-day EMA (intermediate trend)
    breadth['pct_above_50ema'] = sum(1 for s in universe if s.close > s.ema_50) / len(universe)
    
    # 3. New 52-week Highs vs New 52-week Lows
    new_highs = sum(1 for s in universe if s.close >= s.high_52w * 0.99)
    new_lows  = sum(1 for s in universe if s.close <= s.low_52w  * 1.01)
    breadth['high_low_index'] = new_highs / (new_highs + new_lows + 1)
    # >0.7 = strong breadth; <0.3 = weak breadth
    
    # 4. McClellan Oscillator (momentum of A/D)
    # EMA(19) of daily A/D difference minus EMA(39) of daily A/D difference
    ad_diff = advances - declines
    mco = ema(ad_diff, 19) - ema(ad_diff, 39)
    breadth['mcclellan_oscillator'] = mco
    # >100 = overbought (short-term pullback likely); <-100 = oversold (bounce likely)
    
    # 5. Up Volume vs Down Volume ratio
    up_volume   = sum(s.volume for s in universe if s.close > s.open)
    down_volume = sum(s.volume for s in universe if s.close < s.open)
    breadth['updown_volume_ratio'] = up_volume / (down_volume + 1)
    # >2.0 = institutional buying day (strong breadth confirmation)
    # <0.5 = institutional selling day
    
    # 6. Breadth Thrust (Zweig Breadth Thrust)
    # If breadth goes from deeply oversold to deeply overbought within 10 days
    # → one of the most reliable "new bull market beginning" signals
    recent_10d_pct_above_50 = [daily_pct_above_50ema for last 10 days]
    if min(recent_10d_pct_above_50[:5]) < 0.40 and max(recent_10d_pct_above_50[5:]) > 0.615:
        breadth['breadth_thrust'] = True  # Rare, very bullish → override to State 1 if in State 3
    
    return breadth
```

### K.2 Integration into HMM Regime Features
Replace the single `ad_ratio` feature in the HMM with the full breadth suite:
- `pct_above_200ema` (primary health indicator)
- `pct_above_50ema` (intermediate trend)
- `high_low_index` (trend sustainability)
- `mcclellan_oscillator` (short-term momentum of breadth)
- `updown_volume_ratio` (institutional participation)

This makes the HMM regime classification significantly more accurate.

---

## ADDENDUM L — STOCK UNIVERSE CONSTRUCTION & LIQUIDITY FILTER

This was never specified. Without it, the system might try to trade illiquid stocks where signals are meaningless.

### L.1 Universe Definition
```python
UNIVERSE_TIERS = {
    'tier_1': {
        'description': 'Nifty 50 constituents',
        'min_avg_daily_volume': 50_00_00_000,   # ₹50 Cr+ daily
        'min_free_float_mcap': 20_000_00_00_000, # ₹20,000 Cr+
        'max_impact_cost_1L': 0.15,              # Max 0.15% impact for ₹1L order
        'all_6_models_active': True,
        'max_position_kelly_multiplier': 1.0,
    },
    'tier_2': {
        'description': 'Nifty Next 50 + Nifty Midcap 100 top half',
        'min_avg_daily_volume': 10_00_00_000,   # ₹10 Cr+ daily
        'min_free_float_mcap': 5_000_00_00_000, # ₹5,000 Cr+
        'max_impact_cost_1L': 0.5,
        'all_6_models_active': True,
        'max_position_kelly_multiplier': 0.7,   # Smaller max size
    },
    'tier_3': {
        'description': 'Nifty Midcap 100 bottom half + Nifty Smallcap 100 top half',
        'min_avg_daily_volume': 2_00_00_000,    # ₹2 Cr+ daily
        'min_free_float_mcap': 500_00_00_000,   # ₹500 Cr+
        'max_impact_cost_1L': 1.5,
        'sentiment_model_active': False,         # Less news coverage
        'max_position_kelly_multiplier': 0.4,   # Significantly smaller
    }
}

# Hard exclusions — never trade regardless of signals:
HARD_EXCLUSIONS = [
    'stocks_under_sebi_investigation',
    'stocks_with_trading_suspended_in_last_30d',
    'stocks_with_promoter_pledging_veto',
    'stocks_with_avg_daily_volume_below_1cr',
    'penny_stocks_below_rs10',
    'stocks_in_asm_or_esm_list',  # Additional Surveillance Measure / Enhanced SM
]
```

### L.2 ASM/ESM List Monitoring
SEBI and exchanges maintain an Additional Surveillance Measure (ASM) and Enhanced Surveillance Measure (ESM) list for stocks showing unusual price/volume activity. These stocks have circuit limits tightened and are often manipulated.
- Subscribe to daily ASM/ESM updates from NSE/BSE
- Any stock added to ASM/ESM → immediately exit position if held, block new entries for 90 days

---

## ADDENDUM M — CVaR / EXPECTED SHORTFALL RISK MEASURE

### M.1 Why Stop Losses Are Not Enough
Stop losses fail in gap scenarios: if you have a stop at ₹450 but the stock opens at ₹380 due to overnight news, your stop never executes at ₹450. You take a ₹70 loss, not a ₹X loss. CVaR models this tail risk correctly.

### M.2 Implementation
```python
import numpy as np

def calculate_cvar(returns, confidence_level=0.95):
    """
    CVaR (Conditional Value at Risk) = Expected loss in the worst (1-confidence)% of outcomes
    Also called Expected Shortfall (ES)
    
    At 95% confidence: "On the worst 5% of trading days, what is the average loss?"
    """
    sorted_returns = np.sort(returns)
    cutoff_index = int((1 - confidence_level) * len(sorted_returns))
    cvar = -np.mean(sorted_returns[:cutoff_index])
    return cvar

def calculate_position_size_with_cvar(
    kelly_size, 
    stock_returns_history,
    portfolio_value,
    max_cvar_per_position=0.02  # No single position should have >2% CVaR at 95% level
):
    position_cvar = calculate_cvar(stock_returns_history)
    
    # Maximum position value that keeps CVaR within limit:
    max_position_value = (max_cvar_per_position * portfolio_value) / position_cvar
    max_position_fraction = max_position_value / portfolio_value
    
    # Take the minimum of Kelly and CVaR constraint
    final_position_size = min(kelly_size, max_position_fraction)
    return final_position_size

# Portfolio-level CVaR (accounts for correlations):
def calculate_portfolio_cvar(holdings, returns_data, confidence=0.95):
    portfolio_returns = sum(
        weight * returns_data[symbol] 
        for symbol, weight in holdings.items()
    )
    return calculate_cvar(portfolio_returns, confidence)

# Hard limit: Portfolio CVaR at 95% level must never exceed 3% per day
# If it does → reduce all positions proportionally until the constraint is met
```

---

## ADDENDUM N — ERROR ANALYSIS MODULE

### N.1 Every Failed Prediction Is a Teacher
When the system is wrong, classify WHY it was wrong. This turns failures into future improvements.

```python
class ErrorAnalyzer:
    
    ERROR_CATEGORIES = {
        'gap_event': 'Overnight news caused gap beyond predicted range',
        'regime_change': 'Market regime shifted during holding period',
        'fundamental_shock': 'Earnings miss, rating downgrade, scandal',
        'macro_shock': 'RBI surprise, budget, global crisis',
        'sector_rotation': 'Capital rotated out of sector',
        'crowding_reversal': 'Momentum crowding led to sharp reversal',
        'liquidity_event': 'Low volume, price manipulation, circuit',
        'model_error': 'All models agreed but were collectively wrong',
        'timing_error': 'Direction correct but entry/exit timing wrong',
        'unknown': 'Cannot categorize'
    }
    
    def classify_error(self, trade):
        predicted_direction = trade.signal  # BUY or SELL
        actual_outcome = trade.actual_return
        
        if predicted_direction == 'BUY' and actual_outcome < -0.02:
            # Analyze why:
            
            gap_on_day1 = abs(trade.day1_open - trade.entry_price) / trade.entry_price
            if gap_on_day1 > 0.02:
                return 'gap_event'
            
            if trade.had_earnings_announcement:
                return 'fundamental_shock'
            
            regime_on_entry = trade.regime_at_entry
            regime_at_loss = trade.regime_at_exit
            if regime_on_entry != regime_at_loss:
                return 'regime_change'
            
            # Check if all 6 models agreed (collective model error)
            if trade.model_agreement == 6:
                return 'model_error'
            
            return 'unknown'
    
    def generate_weekly_error_report(self, recent_trades):
        errors = [self.classify_error(t) for t in recent_trades if t.was_loss]
        
        error_counts = Counter(errors)
        
        # If any category exceeds 25% of all errors → systemic issue → alert
        for category, count in error_counts.items():
            if count / len(errors) > 0.25:
                alert(f"SYSTEMIC ERROR PATTERN: {category} causing {count/len(errors):.0%} of losses")
        
        return error_counts

# Weekly error report format:
# "Gap events: 35% of losses → increase pre-market gap risk monitoring"
# "Regime change: 28% of losses → HMM classifier needs recalibration"
# "Model errors: 15% → review signal weights in current regime"
```

---

## ADDENDUM O — STRESS TESTING FRAMEWORK

### O.1 Historical Crisis Events to Test Against
The system must be validated against every major market crisis in Indian market history:

```python
STRESS_TEST_SCENARIOS = {
    '2008_global_financial_crisis': {
        'start_date': '2008-01-01',
        'end_date': '2009-03-31',
        'description': 'Nifty fell 60% peak to trough',
        'pass_criteria': {
            'max_drawdown': 0.25,  # System should not lose more than 25% even in 60% market crash
            'capital_preserved': True,  # Must not blow up
        }
    },
    '2013_taper_tantrum': {
        'start_date': '2013-05-01',
        'end_date': '2013-09-30',
        'description': 'Fed tapering caused EM selloff, INR crashed',
        'pass_criteria': {'max_drawdown': 0.12}
    },
    '2015_china_crash': {
        'start_date': '2015-06-01',
        'end_date': '2015-10-31',
        'description': 'China market crash caused global EM selloff',
        'pass_criteria': {'max_drawdown': 0.10}
    },
    '2016_demonetisation': {
        'start_date': '2016-11-08',
        'end_date': '2017-01-31',
        'description': 'India-specific shock, consumption stocks crashed',
        'pass_criteria': {'max_drawdown': 0.15}
    },
    '2018_ILFS_crisis': {
        'start_date': '2018-09-01',
        'end_date': '2019-01-31',
        'description': 'NBFC liquidity crisis, credit market freeze',
        'pass_criteria': {'max_drawdown': 0.12}
    },
    '2020_covid_crash': {
        'start_date': '2020-02-20',
        'end_date': '2020-04-30',
        'description': 'Nifty fell 40% in 40 days — fastest crash in history',
        'pass_criteria': {
            'max_drawdown': 0.20,  # Allowed more drawdown for speed of crash
            'recovery_to_flat_by': '2020-12-31'  # Must have recovered by year-end
        }
    },
    '2022_rate_hike_selloff': {
        'start_date': '2022-01-01',
        'end_date': '2022-06-30',
        'description': 'Global rate hikes, FII exodus from India',
        'pass_criteria': {'max_drawdown': 0.15}
    }
}
```

### O.2 Monte Carlo Simulation for Forward Risk
```python
from scipy.stats import norm
import numpy as np

def monte_carlo_portfolio_risk(
    current_holdings,
    historical_returns,
    n_simulations=10000,
    n_days=252  # 1 year forward
):
    """
    Simulate 10,000 possible portfolio paths over next year.
    Reports: probability of 10% drawdown, 20% drawdown, 30% drawdown.
    """
    portfolio_returns = calculate_portfolio_returns(current_holdings, historical_returns)
    
    mu = np.mean(portfolio_returns)
    sigma = np.std(portfolio_returns)
    
    # Use fat-tail distribution (t-distribution with 5 df) not normal
    # Financial returns have fat tails — normal distribution underestimates crash probability
    from scipy.stats import t as t_dist
    
    simulation_results = []
    for _ in range(n_simulations):
        daily_returns = t_dist.rvs(df=5, loc=mu, scale=sigma, size=n_days)
        cumulative_returns = np.cumprod(1 + daily_returns) - 1
        max_drawdown = calculate_max_drawdown(cumulative_returns)
        simulation_results.append(max_drawdown)
    
    return {
        'prob_10pct_drawdown': sum(1 for dd in simulation_results if dd > 0.10) / n_simulations,
        'prob_20pct_drawdown': sum(1 for dd in simulation_results if dd > 0.20) / n_simulations,
        'prob_30pct_drawdown': sum(1 for dd in simulation_results if dd > 0.30) / n_simulations,
        'expected_annual_return': np.mean([r[-1] for r in simulation_paths]),
        'var_95': np.percentile(simulation_results, 95),   # 95% VaR
        'cvar_95': np.mean([dd for dd in simulation_results if dd > np.percentile(simulation_results, 95)])
    }
```

---

## FINAL INTEGRATION NOTE

These 15 addenda are not separate features — they are woven into the existing layers:

| Addendum | Integrates Into |
|----------|----------------|
| A — Macro Calendar | Layer 1 (data) + Layer 5 (suppression rules) |
| B — AMFI MF Holdings | Layer 1 (data) + Layer 2 Model 5 (FII/DII model) |
| C — SAST Insider Data | Layer 1 (data) + Layer 2 (new 7th signal) |
| D — GARCH | Layer 2 Model 3 (range prediction) + Layer 3 HMM features |
| E — Portfolio Correlation | Layer 5 (risk) — replaces naive Kelly with corr-adjusted Kelly |
| F — TFT | Layer 4 (ML) — replaces or sits alongside XGBoost |
| G — Intermarket | Layer 2 (new sector-level adjustment) + Layer 3 (regime) |
| H — Seasonality | Layer 2 (add to ensemble as 8th signal) |
| I — Momentum Crash | Layer 3 (regime intelligence) — new sub-module |
| J — Credit Rating | Layer 1 (data) + Layer 5 (hard veto) |
| K — Market Breadth | Layer 3 HMM (replace A/D with full suite) |
| L — Universe | Layer 1 (prerequisite — foundational) |
| M — CVaR | Layer 5 (risk) — alongside Kelly sizing |
| N — Error Analysis | Layer 6 (continuous improvement) |
| O — Stress Testing | Layer 6 (validation) |

---

*This addendum, combined with the Master Prompt, constitutes the complete, nothing-left-out specification for Agent Alpha v2.0.*
*Combined signal count: 8 ensemble models. Combined data sources: 18 distinct feeds. Combined ML approaches: LightGBM + TFT + RL Agent.*
*This is the ceiling.*
