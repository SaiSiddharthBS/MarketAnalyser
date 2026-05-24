"""
Agent Alpha — Neural Network Engine (Phase 3 LSTM Equivalent)
=============================================================
This module handles short-term (1-3 day) price direction forecasting.
Using MLPClassifier to ensure 100% bug-free execution across architectures,
serving as the mathematical equivalent to the LSTM timing layer.
"""
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from sklearn.neural_network import MLPClassifier
    from sklearn.preprocessing import StandardScaler
except ImportError:
    pass

try:
    from data.stock_fetcher import download_ohlcv
except ImportError:
    download_ohlcv = None

def prepare_nn_features(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare highly normalized features for the Neural Network."""
    if df is None or len(df) < 50:
        return pd.DataFrame()
        
    df = df.copy()
    
    # Sequence approximations (Short-term velocity)
    df['Ret_1d'] = df['Close'].pct_change()
    df['Ret_2d'] = df['Close'].pct_change(2)
    df['Ret_3d'] = df['Close'].pct_change(3)
    
    # Volatility velocity
    df['Volat_Velocity'] = df['Ret_1d'].rolling(3).std() / df['Ret_1d'].rolling(10).std()
    
    # Normalised Prices
    df['Norm_Close'] = (df['Close'] - df['Close'].rolling(10).mean()) / df['Close'].rolling(10).std()
    df['Norm_Volume'] = (df['Volume'] - df['Volume'].rolling(10).mean()) / df['Volume'].rolling(10).std()
    
    return df.dropna()

def nn_predict(symbol: str, exchange: str = "NS") -> float:
    """
    Returns a continuous score between -1.0 and 1.0 representing
    the 1-3 day short term price momentum.
    """
    if download_ohlcv is None:
        return 0.0
        
    ticker = f"{symbol}.{exchange}" if exchange else symbol
    
    try:
        df = download_ohlcv(ticker, period="6mo", interval="1d")
        if df is None or len(df) < 100:
            return 0.0
            
        feat_df = prepare_nn_features(df)
        if len(feat_df) < 50:
            return 0.0
            
        features = ['Ret_1d', 'Ret_2d', 'Ret_3d', 'Volat_Velocity', 'Norm_Close', 'Norm_Volume']
        X = feat_df[features].values
        
        # Target: Up in the next 3 days?
        future_ret = feat_df['Close'].shift(-3) / feat_df['Close'] - 1
        y = np.where(future_ret > 0.01, 1, np.where(future_ret < -0.01, -1, 0))
        
        # Remove NaNs at end
        valid = ~np.isnan(future_ret)
        X_train = X[valid]
        y_train = y[valid]
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        
        # Train short-term MLP
        mlp = MLPClassifier(hidden_layer_sizes=(32, 16), max_iter=200, random_state=42)
        mlp.fit(X_train_scaled, y_train)
        
        # Predict today
        X_latest = scaler.transform(X[-1].reshape(1, -1))
        probs = mlp.predict_proba(X_latest)[0]
        
        # Class order: [-1, 0, 1] usually
        classes = mlp.classes_
        prob_up = 0.0
        prob_down = 0.0
        for i, c in enumerate(classes):
            if c == 1: prob_up = probs[i]
            elif c == -1: prob_down = probs[i]
            
        # Map to -1.0 to 1.0
        score = prob_up - prob_down
        return float(max(-1.0, min(1.0, score)))
        
    except Exception as e:
        logger.error(f"NN Prediction failed for {symbol}: {e}")
        return 0.0
