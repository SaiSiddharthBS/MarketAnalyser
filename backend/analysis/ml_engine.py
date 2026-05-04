"""
MarketPulse — Machine Learning Engine
Trains and runs XGBoost models to predict short-to-medium term price movements.
"""
import pandas as pd
import numpy as np
import yfinance as yf
import ta
import joblib
import os
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from datetime import datetime

# Use the shared robust downloader with Yahoo API fallback
from data.stock_fetcher import download_ohlcv

# Setup models directory
MODELS_DIR = Path(__file__).parent.parent.parent / "data" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

def prepare_features(df):
    """Calculate technical indicators as features for the ML model."""
    if df.empty or len(df) < 200:
        return None

    # RSI
    df["RSI"] = ta.momentum.RSIIndicator(df["Close"], window=14).rsi()
    
    # MACD
    macd = ta.trend.MACD(df["Close"])
    df["MACD"] = macd.macd()
    df["MACD_Hist"] = macd.macd_diff()
    
    # EMAs
    df["EMA_20"] = ta.trend.EMAIndicator(df["Close"], window=20).ema_indicator()
    df["EMA_50"] = ta.trend.EMAIndicator(df["Close"], window=50).ema_indicator()
    df["EMA_200"] = ta.trend.EMAIndicator(df["Close"], window=200).ema_indicator()
    
    # Distance from EMAs (%)
    df["Dist_EMA20"] = (df["Close"] - df["EMA_20"]) / df["EMA_20"] * 100
    df["Dist_EMA50"] = (df["Close"] - df["EMA_50"]) / df["EMA_50"] * 100
    df["Dist_EMA200"] = (df["Close"] - df["EMA_200"]) / df["EMA_200"] * 100
    
    # Bollinger Bands
    bb = ta.volatility.BollingerBands(df["Close"], window=20)
    df["BB_Width"] = (bb.bollinger_hband() - bb.bollinger_lband()) / df["Close"] * 100
    df["BB_Pos"] = (df["Close"] - bb.bollinger_lband()) / (bb.bollinger_hband() - bb.bollinger_lband())
    
    # ATR & Volatility
    df["ATR"] = ta.volatility.AverageTrueRange(df["High"], df["Low"], df["Close"]).average_true_range()
    df["Volatility"] = df["Close"].pct_change().rolling(window=20).std() * 100
    
    # Price Momentum (Returns)
    df["Ret_1d"] = df["Close"].pct_change(1)
    df["Ret_5d"] = df["Close"].pct_change(5)
    df["Ret_10d"] = df["Close"].pct_change(10)
    df["Ret_20d"] = df["Close"].pct_change(20)
    
    # Volume Momentum
    df["Vol_Change"] = df["Volume"].pct_change(1)
    df["Vol_MA20"] = df["Volume"].rolling(window=20).mean()
    df["Vol_Ratio"] = df["Volume"] / df["Vol_MA20"]
    
    return df.dropna()

def fetch_and_prepare_data(symbol, exchange="NS", period="5y"):
    """Fetch history, generate features, and create target."""
    ticker = f"{symbol}.{exchange}" if exchange else symbol
    try:
        df = download_ohlcv(ticker, period=period)
            
        df = prepare_features(df)
        if df is None or len(df) < 100:
            return None, None
            
        # Target: Will the price be at least 2% higher in 10 days?
        horizon = 10
        target_return = 0.02
        
        # Calculate future returns
        df[f"Future_Ret_{horizon}d"] = df["Close"].shift(-horizon) / df["Close"] - 1
        
        # Binary target: 1 if Up > target_return, else 0
        df["Target"] = (df[f"Future_Ret_{horizon}d"] > target_return).astype(int)
        
        # Drop the last 'horizon' rows since we don't know the future yet
        df_train = df.iloc[:-horizon].copy()
        df_latest = df.iloc[[-1]].copy() # The absolute latest row for today's prediction
        
        return df_train, df_latest
    except Exception as e:
        print(f"Error preparing ML data for {symbol}: {e}")
        return None, None

def train_model_for_symbol(symbol, exchange="NS"):
    """Train XGBoost for a specific stock."""
    df_train, df_latest = fetch_and_prepare_data(symbol, exchange)
    if df_train is None:
        return False
        
    features = [
        "RSI", "MACD", "MACD_Hist", "Dist_EMA20", "Dist_EMA50", "Dist_EMA200", 
        "BB_Width", "BB_Pos", "ATR", "Volatility", 
        "Ret_1d", "Ret_5d", "Ret_10d", "Ret_20d", "Vol_Ratio"
    ]
    
    X = df_train[features]
    y = df_train["Target"]
    
    # Train model
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=5,
        min_samples_split=5,
        random_state=42,
        class_weight='balanced'
    )
    model.fit(X, y)
    
    # Save model
    model_path = MODELS_DIR / f"{symbol}_rf.joblib"
    joblib.dump(model, model_path)
    
    # Calculate feature importance
    importance = {f: float(imp) for f, imp in zip(features, model.feature_importances_)}
    importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True)[:3])
    
    return True, importance

def predict_symbol(symbol, exchange="NS"):
    """Predict the probability of an upward move for a stock."""
    model_path = MODELS_DIR / f"{symbol}_rf.joblib"
    
    # If model doesn't exist, train it (first run will be slower)
    if not model_path.exists():
        success, imp = train_model_for_symbol(symbol, exchange)
        if not success:
            return None
            
    try:
        model = joblib.load(model_path)
    except Exception:
        # Corrupted model? Retrain
        train_model_for_symbol(symbol, exchange)
        model = joblib.load(model_path)
        
    df_train, df_latest = fetch_and_prepare_data(symbol, exchange, period="2y")
    if df_latest is None:
        return None
        
    features = [
        "RSI", "MACD", "MACD_Hist", "Dist_EMA20", "Dist_EMA50", "Dist_EMA200", 
        "BB_Width", "BB_Pos", "ATR", "Volatility", 
        "Ret_1d", "Ret_5d", "Ret_10d", "Ret_20d", "Vol_Ratio"
    ]
    
    X_pred = df_latest[features]
    
    # Get probability of class 1 (Upward move)
    prob = model.predict_proba(X_pred)[0]
    prob_down, prob_up = prob[0], prob[1]
    
    return {
        "symbol": symbol,
        "prob_up": float(prob_up),
        "prob_down": float(prob_down),
        "horizon": 10,
        "target_return": 2.0, # 2%
        "date": datetime.now().strftime("%Y-%m-%d"),
        "confidence_level": "HIGH" if prob_up > 0.65 or prob_down > 0.65 else "LOW"
    }

if __name__ == "__main__":
    print("Testing ML Engine on RELIANCE...")
    res = predict_symbol("RELIANCE")
    print(res)
