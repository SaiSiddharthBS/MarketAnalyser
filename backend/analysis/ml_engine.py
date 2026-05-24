"""
Agent Alpha v2.0 — Machine Learning Decision Engine (LightGBM)
===============================================================
Complete rebuild from v1's RandomForest.

Why LightGBM over RandomForest:
- 10× faster training
- Handles categorical features natively
- Better gradient optimization (GBDT > bagging)
- Lower memory footprint
- Same CPU requirements (no GPU needed)

CRITICAL: Walk-Forward Cross-Validation
- NEVER use random train/test split for time-series data
- Random split = look-ahead bias = backtest fraud
- TimeSeriesSplit with 5-day gap = production-grade validation

Features: All 8 model scores + regime + VIX + FII flow + delivery %
          + PCR + days to expiry + sector RS + RVOL + macro suppression

Target: 3-class classification
    +1 = stock goes up >2% in 5 trading days
     0 = stock stays within ±2%
    -1 = stock goes down >2% in 5 trading days
"""
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

try:
    import lightgbm as lgb
    LGBM_AVAILABLE = True
except ImportError:
    LGBM_AVAILABLE = False
    # Fallback to sklearn GradientBoosting
    from sklearn.ensemble import GradientBoostingClassifier

from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, classification_report

import ta

try:
    from data.stock_fetcher import download_ohlcv
except ImportError:
    download_ohlcv = None

MODELS_DIR = Path(__file__).parent.parent.parent / "data" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Feature set for the ML model
FEATURE_COLUMNS = [
    # Technical indicators
    "RSI", "MACD", "MACD_Hist", "ADX",
    "Dist_EMA20", "Dist_EMA50", "Dist_EMA200",
    "BB_Width", "BB_Pos",
    "ATR_Pct",  # ATR as % of close price
    "Volatility_20d",
    # Price momentum
    "Ret_1d", "Ret_5d", "Ret_10d", "Ret_20d",
    # Volume
    "Vol_Ratio", "Vol_Change_5d",
    # Microstructure
    "OFI_proxy",  # Order flow imbalance
    "OFI_cumulative_5d",
    # Relative strength
    "RS_vs_Nifty_20d",
]


def prepare_ml_features(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Phase 3: Upgraded Feature Engineering Pipeline.
    Delegates to the new feature_engineer.py which generates 50+ features.
    """
    try:
        from analysis.feature_engineer import generate_50_features
        df_features = generate_50_features(df)
        return df_features
    except ImportError:
        return None


def create_target_variable(
    df: pd.DataFrame,
    horizon: int = 5,
    threshold_pct: float = 2.0,
) -> pd.Series:
    """
    Create 3-class target variable.

    +1 = stock goes up > threshold% in horizon days
     0 = stock stays within ±threshold%
    -1 = stock goes down > threshold% in horizon days

    Args:
        df: DataFrame with 'Close' column
        horizon: Forward-looking horizon in trading days
        threshold_pct: Minimum move for +1/-1 classification

    Returns:
        Series of target labels (-1, 0, +1)
    """
    future_return = df["Close"].shift(-horizon) / df["Close"] - 1
    future_return_pct = future_return * 100

    target = pd.Series(0, index=df.index)
    target[future_return_pct > threshold_pct] = 1
    target[future_return_pct < -threshold_pct] = -1

    return target


def train_model(
    symbol: str,
    exchange: str = "NS",
    n_splits: int = 10,
    gap: int = 5,
) -> Tuple[bool, Dict[str, Any]]:
    """
    Train LightGBM with walk-forward cross-validation.

    This is the CORRECT way to validate time-series ML models:
    - TimeSeriesSplit ensures no future data leaks into training
    - Gap of 5 days prevents target leakage at split boundaries

    Args:
        symbol: Stock symbol
        exchange: Exchange suffix
        n_splits: Number of CV splits (default 10)
        gap: Gap between train and test (default 5 days)

    Returns:
        Tuple of (success, metrics_dict)
    """
    if download_ohlcv is None:
        return False, {"error": "download_ohlcv not available"}

    ticker = f"{symbol}.{exchange}" if exchange else symbol

    try:
        df = download_ohlcv(ticker, period="5y")
        if df is None or len(df) < 500:
            return False, {"error": f"Insufficient data: {len(df) if df is not None else 0} rows"}

        df_features = prepare_ml_features(df)
        if df_features is None or len(df_features) < 400:
            return False, {"error": "Feature preparation failed"}

        # Create target
        target = create_target_variable(df_features, horizon=5, threshold_pct=2.0)

        # Remove rows where target is NaN (last 5 rows)
        valid_mask = target.notna()
        df_train = df_features[valid_mask]
        y = target[valid_mask]

        # Extract feature columns automatically since Phase 3 generates 50+ dynamically
        feat_cols = [c for c in df_train.columns if c not in ['Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close']]
        X = df_train[feat_cols]

        # ─── Walk-Forward Cross-Validation ───────────────────
        tscv = TimeSeriesSplit(n_splits=n_splits, gap=gap)
        cv_scores = []
        cv_reports = []

        for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

            try:
                import xgboost as xgb
                model = xgb.XGBClassifier(
                    n_estimators=200, learning_rate=0.05, max_depth=5, 
                    subsample=0.8, random_state=42, use_label_encoder=False, eval_metric='mlogloss'
                )
            except ImportError:
                model = GradientBoostingClassifier(
                    n_estimators=200, learning_rate=0.05, max_depth=5,
                    min_samples_split=50, subsample=0.8, random_state=42
                )

            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            acc = accuracy_score(y_test, y_pred)
            cv_scores.append(acc)

        # ─── Train Final Model on All Data ───────────────────
        try:
            import xgboost as xgb
            final_model = xgb.XGBClassifier(
                n_estimators=200, learning_rate=0.05, max_depth=5, 
                subsample=0.8, random_state=42, use_label_encoder=False, eval_metric='mlogloss'
            )
        except ImportError:
            final_model = GradientBoostingClassifier(
                n_estimators=200, learning_rate=0.05, max_depth=5,
                min_samples_split=50, subsample=0.8, random_state=42
            )

        final_model.fit(X, y)

        # Save model
        model_path = MODELS_DIR / f"{symbol}_lgbm.joblib"
        joblib.dump(final_model, model_path)

        # Feature importance
        importances = dict(zip(feat_cols, final_model.feature_importances_))
        top_features = dict(sorted(importances.items(), key=lambda x: x[1], reverse=True)[:5])

        metrics = {
            "cv_accuracy_mean": round(float(np.mean(cv_scores)), 4),
            "cv_accuracy_std": round(float(np.std(cv_scores)), 4),
            "cv_scores": [round(s, 4) for s in cv_scores],
            "n_splits": n_splits,
            "gap": gap,
            "total_samples": len(X),
            "class_distribution": dict(y.value_counts()),
            "top_features": top_features,
            "model_type": "XGBoost (or fallback)",
            "trained_at": datetime.now().isoformat(),
        }

        print(f"✅ ML Model trained for {symbol}: CV accuracy {metrics['cv_accuracy_mean']:.1%} ± {metrics['cv_accuracy_std']:.1%}")
        return True, metrics

    except Exception as e:
        print(f"❌ ML training failed for {symbol}: {e}")
        return False, {"error": str(e)}


def predict_symbol(
    symbol: str,
    exchange: str = "NS",
) -> Optional[Dict[str, Any]]:
    """
    Generate ML prediction for a stock.

    Returns:
        Dict with: prob_up, prob_down, prob_flat, ml_signal, confidence
    """
    model_path = MODELS_DIR / f"{symbol}_lgbm.joblib"

    if not model_path.exists():
        success, _ = train_model(symbol, exchange)
        if not success:
            return None

    try:
        model = joblib.load(model_path)
    except Exception:
        success, _ = train_model(symbol, exchange)
        if not success:
            return None
        model = joblib.load(model_path)

    # Get latest features
    ticker = f"{symbol}.{exchange}" if exchange else symbol
    try:
        df = download_ohlcv(ticker, period="2y")
        df_features = prepare_ml_features(df)
        if df_features is None or df_features.empty:
            return None

        feat_cols = [c for c in df_features.columns if c not in ['Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close']]
        X_latest = df_features[feat_cols].iloc[[-1]]

        # Predict probabilities
        probs = model.predict_proba(X_latest)[0]
        classes = model.classes_

        prob_dict = {}
        for cls, prob in zip(classes, probs):
            if cls == 1:
                prob_dict["prob_up"] = float(prob)
            elif cls == -1:
                prob_dict["prob_down"] = float(prob)
            else:
                prob_dict["prob_flat"] = float(prob)

        # Fill defaults if class missing
        prob_up = prob_dict.get("prob_up", 0.33)
        prob_down = prob_dict.get("prob_down", 0.33)
        prob_flat = prob_dict.get("prob_flat", 0.34)

        # ML signal
        prediction = model.predict(X_latest)[0]
        if prediction == 1:
            ml_signal = "BUY"
        elif prediction == -1:
            ml_signal = "SELL"
        else:
            ml_signal = "NEUTRAL"

        confidence = max(prob_up, prob_down, prob_flat) * 100

        return {
            "symbol": symbol,
            "ml_signal": ml_signal,
            "prob_up": round(prob_up, 4),
            "prob_down": round(prob_down, 4),
            "prob_flat": round(prob_flat, 4),
            "confidence": round(confidence, 1),
            "prediction_class": int(prediction),
            "horizon_days": 5,
            "target_return_pct": 2.0,
            "date": datetime.now().strftime("%Y-%m-%d"),
        }

    except Exception as e:
        print(f"❌ ML prediction failed for {symbol}: {e}")
        return None
