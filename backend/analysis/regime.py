"""
Agent Alpha v2.0 — HMM Regime Classifier (Layer 3)
===================================================
A 4-state Hidden Markov Model that probabilistically identifies the 
true underlying market regime using multiple observable features.

Why HMM?
Simple rules (like "if price < 200 EMA then bear market") whipsaw constantly.
HMMs recognize that regimes are "hidden" states that emit observable features
(like returns, volatility, and breadth). They provide a probability for each
regime, allowing us to size positions continuously rather than binary on/off.

The 4 States:
1. Low-Vol Uptrend (Home Turf) → Full Kelly sizing
2. High-Vol Uptrend (Cautious Bull) → 0.6× Kelly
3. Low-Vol Chop (Stand Aside/Mean Reversion) → 0.3× Kelly, no momentum
4. Crisis/Crash (Survival Mode) → 0.0× Kelly (cash), tight stops

Features fed into HMM:
- Daily Nifty Returns
- 20-day Realized Volatility
- VIX closing value
- Market Breadth (McClellan approximation)
- Distance from 200 EMA
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import warnings

try:
    from hmmlearn import hmm
    HMM_AVAILABLE = True
except ImportError:
    HMM_AVAILABLE = False
    warnings.warn("hmmlearn is not installed. Regime classifier will use rule-based fallback.")

try:
    from data.stock_fetcher import download_ohlcv
except ImportError:
    download_ohlcv = None


class RegimeClassifier:
    """Hidden Markov Model for Market Regime Classification."""

    def __init__(self, n_components: int = 4, random_state: int = 42):
        self.n_components = n_components
        self.model = None
        self.is_fitted = False
        
        # We will map the HMM's arbitrary state numbers (0, 1, 2, 3) 
        # to our semantic states based on their statistical properties.
        self.state_map = {}
        
        if HMM_AVAILABLE:
            # Gaussian HMM with full covariance matrix
            self.model = hmm.GaussianHMM(
                n_components=n_components,
                covariance_type="full",
                n_iter=1000,
                random_state=random_state,
            )

    def prepare_features(self, nifty_df: pd.DataFrame, vix_df: pd.DataFrame, breadth_series: pd.Series = None) -> pd.DataFrame:
        """
        Prepare observable features for the HMM.
        """
        if nifty_df is None or len(nifty_df) < 252:
            return pd.DataFrame()
            
        df = nifty_df.copy()
        
        # 1. Daily Returns
        df["Return"] = df["Close"].pct_change()
        
        # 2. 20-day Realized Volatility
        df["Vol_20d"] = df["Return"].rolling(20).std() * np.sqrt(252)
        
        # 3. Distance from 200 EMA
        ema200 = df["Close"].ewm(span=200, adjust=False).mean()
        df["Dist_EMA200"] = (df["Close"] - ema200) / ema200
        
        # 4. VIX 
        if vix_df is not None and not vix_df.empty:
            df = df.join(vix_df["Close"].rename("VIX"), how="left")
            df["VIX"] = df["VIX"].ffill() # Forward fill missing VIX days
        else:
            # Proxy VIX from realized vol if real VIX is missing
            df["VIX"] = df["Vol_20d"] * 100
            
        # 5. Breadth (if available, otherwise use a placeholder)
        if breadth_series is not None:
            df["Breadth"] = breadth_series
        else:
            # Proxy breadth using 20-day return of the index itself
            df["Breadth"] = df["Close"].pct_change(20)
            
        df = df.dropna()
        return df

    def fit(self, features_df: pd.DataFrame) -> bool:
        """
        Train the HMM on historical features and map the semantic states.
        """
        if not HMM_AVAILABLE or features_df.empty:
            return False
            
        # Select columns for HMM
        feature_cols = ["Return", "Vol_20d", "VIX", "Dist_EMA200", "Breadth"]
        X = features_df[feature_cols].values
        
        try:
            self.model.fit(X)
            self.is_fitted = True
            
            # ─── Map Arbitrary States to Semantic Regimes ───────────
            # The HMM assigns states 0, 1, 2, 3 randomly. We need to identify
            # which one is the crisis state, which is the bull state, etc.
            
            # Predict states for the training data
            hidden_states = self.model.predict(X)
            features_df["State"] = hidden_states
            
            # Calculate mean statistics for each state
            state_stats = features_df.groupby("State").mean()
            
            # We map based on Volatility (VIX) and Trend (Return / Dist_EMA200)
            states = list(range(self.n_components))
            
            # 1. State with highest VIX -> Crisis
            crisis_state = state_stats["VIX"].idxmax()
            states.remove(crisis_state)
            
            # 2. Among remaining, state with lowest Vol_20d -> Low-Vol Chop or Bull
            low_vol_states = sorted(states, key=lambda x: state_stats.loc[x, "Vol_20d"])
            
            # State with lowest vol AND positive return -> Low-Vol Uptrend
            # Let's sort the 3 remaining by Return
            remaining_by_return = sorted(states, key=lambda x: state_stats.loc[x, "Return"], reverse=True)
            
            bull_state = remaining_by_return[0]
            if bull_state in states: states.remove(bull_state)
            
            # Of the 2 remaining, the one with higher vol is High-Vol Uptrend
            if len(states) == 2:
                if state_stats.loc[states[0], "Vol_20d"] > state_stats.loc[states[1], "Vol_20d"]:
                    high_vol_bull = states[0]
                    chop_state = states[1]
                else:
                    high_vol_bull = states[1]
                    chop_state = states[0]
            else:
                high_vol_bull = states[0] if states else -1
                chop_state = states[0] if states else -1
                
            self.state_map = {
                bull_state: "low_vol_uptrend",
                high_vol_bull: "high_vol_uptrend",
                chop_state: "low_vol_chop",
                crisis_state: "crisis"
            }
            
            return True
            
        except Exception as e:
            print(f"❌ HMM Fitting failed: {e}")
            return False

    def predict_current_regime(self, features_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Predict the current market regime based on the latest features.
        """
        if not self.is_fitted or not HMM_AVAILABLE or features_df.empty:
            return self._fallback_rule_based_regime(features_df)
            
        feature_cols = ["Return", "Vol_20d", "VIX", "Dist_EMA200", "Breadth"]
        X = features_df[feature_cols].values
        
        try:
            # Predict state for the most recent day
            latest_X = X[-1].reshape(1, -1)
            state_idx = self.model.predict(latest_X)[0]
            
            # Get probabilities for all states
            probs = self.model.predict_proba(latest_X)[0]
            
            regime_name = self.state_map.get(state_idx, "unknown")
            confidence = probs[state_idx] * 100
            
            # Calculate transition probability to crisis state
            # This is "Regime Transition Probability Matrix" from my 7 additions
            crisis_idx = next((k for k, v in self.state_map.items() if v == "crisis"), None)
            
            crisis_prob_tmr = 0.0
            if crisis_idx is not None:
                # Transition matrix: model.transmat_[current_state, next_state]
                crisis_prob_tmr = self.model.transmat_[state_idx, crisis_idx] * 100
                
            return self._format_regime_output(
                regime_name=regime_name,
                confidence=confidence,
                crisis_transition_prob=crisis_prob_tmr,
                features=features_df.iloc[-1].to_dict(),
                method="HMM"
            )
            
        except Exception as e:
            print(f"❌ HMM Prediction failed: {e}")
            return self._fallback_rule_based_regime(features_df)

    def _fallback_rule_based_regime(self, features_df: pd.DataFrame) -> Dict[str, Any]:
        """
        If HMM fails or isn't available, use a robust rule-based approximation.
        This matches the 4 states of the HMM using strict VIX and EMA rules.
        """
        if features_df is None or features_df.empty:
            return self._format_regime_output("unknown", 0.0, 0.0, {}, "None")
            
        latest = features_df.iloc[-1]
        
        vix = latest.get("VIX", 15.0)
        dist_ema200 = latest.get("Dist_EMA200", 0.0)
        
        if dist_ema200 < 0 or vix >= 25:
            regime = "crisis"
            conf = 80.0
        elif vix < 18 and dist_ema200 > 0.02:
            regime = "low_vol_uptrend"
            conf = 75.0
        elif vix >= 18 and dist_ema200 > 0:
            regime = "high_vol_uptrend"
            conf = 65.0
        else:
            regime = "low_vol_chop"
            conf = 60.0
            
        # Fast VIX spike check for crisis transition
        crisis_prob = 0.0
        if len(features_df) >= 5:
            vix_5d_ago = features_df["VIX"].iloc[-5]
            if vix > vix_5d_ago * 1.2: # 20% spike in 5 days
                crisis_prob = 40.0
                
        return self._format_regime_output(
            regime_name=regime,
            confidence=conf,
            crisis_transition_prob=crisis_prob,
            features=latest.to_dict(),
            method="Rule-Based Fallback"
        )

    def _format_regime_output(self, regime_name: str, confidence: float, 
                              crisis_transition_prob: float, features: Dict, method: str) -> Dict[str, Any]:
        """Standardize the output format for downstream consumption."""
        
        # Map to UI colors and emojis
        visuals = {
            "low_vol_uptrend": {"color": "#10b981", "emoji": "🟢", "status": "Home Turf (Aggressive)"},
            "high_vol_uptrend": {"color": "#3b82f6", "emoji": "📈", "status": "Cautious Bull"},
            "low_vol_chop": {"color": "#f59e0b", "emoji": "🟡", "status": "Mean Reversion / Chop"},
            "crisis": {"color": "#ef4444", "emoji": "🔴", "status": "Crisis / Survival Mode"},
            "unknown": {"color": "#6b7280", "emoji": "⚪", "status": "Unknown"}
        }
        
        vis = visuals.get(regime_name, visuals["unknown"])
        
        return {
            "regime": regime_name,
            "status": vis["status"],
            "color": vis["color"],
            "emoji": vis["emoji"],
            "confidence_pct": round(confidence, 1),
            "crisis_probability_tomorrow_pct": round(crisis_transition_prob, 1),
            "method": method,
            "vix_level": round(features.get("VIX", 0), 2),
            "nifty_vs_200ema_pct": round(features.get("Dist_EMA200", 0) * 100, 2),
            "date": datetime.now().strftime("%Y-%m-%d")
        }


# Global singleton
regime_classifier = RegimeClassifier()
_cached_regime = None
_last_regime_fetch = None

def get_current_market_regime() -> Dict[str, Any]:
    """
    Main entry point for fetching the current market regime.
    Handles downloading data, fitting the HMM if needed, and predicting.
    """
    global _cached_regime, _last_regime_fetch
    from datetime import datetime
    
    now = datetime.now()
    if _cached_regime and _last_regime_fetch:
        if (now - _last_regime_fetch).total_seconds() < 300: # 5 minutes cache
            return _cached_regime

    if download_ohlcv is None:
        return regime_classifier._fallback_rule_based_regime(pd.DataFrame())
        
    try:
        # Download at least 3 years of data for HMM training
        nifty_df = download_ohlcv("^NSEI", period="3y")
        vix_df = download_ohlcv("^INDIAVIX", period="3y")
        
        if nifty_df is None or nifty_df.empty:
            return regime_classifier._fallback_rule_based_regime(pd.DataFrame())
            
        features_df = regime_classifier.prepare_features(nifty_df, vix_df)
        
        if not features_df.empty:
            if not regime_classifier.is_fitted:
                regime_classifier.fit(features_df)
                
            res = regime_classifier.predict_current_regime(features_df)
            _cached_regime = res
            _last_regime_fetch = now
            return res
            
    except Exception as e:
        print(f"❌ Regime calculation failed: {e}")
        
    res = regime_classifier._fallback_rule_based_regime(pd.DataFrame())
    _cached_regime = res
    _last_regime_fetch = now
    return res

def get_smoothed_market_regime() -> Dict[str, Any]:
    """Alias for get_current_market_regime to support older API endpoints."""
    return get_current_market_regime()

