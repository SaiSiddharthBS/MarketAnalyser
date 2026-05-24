import pandas as pd
import numpy as np
import ta

def generate_50_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Phase 3: Proper Feature Engineering Pipeline (50+ engineered features).
    Takes raw OHLCV and returns a rich feature matrix.
    """
    if df is None or len(df) < 60:
        return df
        
    df = df.copy()
    
    # 1. Price Momentum (Returns at multiple horizons)
    for period in [1, 2, 3, 5, 10, 15, 20, 30, 60]:
        df[f'Ret_{period}d'] = df['Close'].pct_change(period)
        
    # 2. Volatility & Ranges
    for period in [5, 10, 20, 60]:
        df[f'Volat_{period}d'] = df['Close'].pct_change().rolling(period).std()
        df[f'HL_Range_{period}d'] = (df['High'].rolling(period).max() - df['Low'].rolling(period).min()) / df['Close']
        
    # 3. Moving Average Distances
    for period in [10, 20, 50, 100, 200]:
        ma = df['Close'].rolling(period).mean()
        df[f'Dist_SMA_{period}'] = (df['Close'] - ma) / ma
        
        ema = df['Close'].ewm(span=period, adjust=False).mean()
        df[f'Dist_EMA_{period}'] = (df['Close'] - ema) / ema
        
    # 4. Volume Features
    for period in [5, 10, 20]:
        vol_ma = df['Volume'].rolling(period).mean()
        df[f'RVOL_{period}d'] = df['Volume'] / vol_ma
        df[f'Vol_Change_{period}d'] = df['Volume'].pct_change(period)
        
    # 5. Technical Indicators (ta library)
    # RSI
    df['RSI_14'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
    df['RSI_7'] = ta.momentum.RSIIndicator(df['Close'], window=7).rsi()
    
    # MACD
    macd = ta.trend.MACD(df['Close'])
    df['MACD'] = macd.macd()
    df['MACD_Hist'] = macd.macd_diff()
    df['MACD_Signal'] = macd.macd_signal()
    
    # Bollinger Bands
    bb = ta.volatility.BollingerBands(df['Close'], window=20, window_dev=2)
    df['BB_Width'] = (bb.bollinger_hband() - bb.bollinger_lband()) / df['Close']
    df['BB_Pct'] = bb.bollinger_pband()
    
    # ATR
    atr = ta.volatility.AverageTrueRange(df['High'], df['Low'], df['Close'], window=14)
    df['ATR_14'] = atr.average_true_range()
    df['ATR_Pct'] = df['ATR_14'] / df['Close']
    
    # OBV (On-Balance Volume)
    obv = ta.volume.OnBalanceVolumeIndicator(df['Close'], df['Volume'])
    df['OBV'] = obv.on_balance_volume()
    df['OBV_Ret_5d'] = df['OBV'].pct_change(5)
    
    # ADX
    adx = ta.trend.ADXIndicator(df['High'], df['Low'], df['Close'], window=14)
    df['ADX'] = adx.adx()
    df['DI_Plus'] = adx.adx_pos()
    df['DI_Minus'] = adx.adx_neg()
    
    # Stochastic Oscillator
    stoch = ta.momentum.StochasticOscillator(df['High'], df['Low'], df['Close'])
    df['Stoch_K'] = stoch.stoch()
    df['Stoch_D'] = stoch.stoch_signal()
    
    # Williams %R
    wr = ta.momentum.WilliamsRIndicator(df['High'], df['Low'], df['Close'])
    df['Williams_R'] = wr.williams_r()
    
    # 6. Microstructure & Price Action
    df['Gap_Pct'] = (df['Open'] - df['Close'].shift(1)) / df['Close'].shift(1)
    df['Upper_Shadow'] = (df['High'] - df[['Open', 'Close']].max(axis=1)) / df['Close']
    df['Lower_Shadow'] = (df[['Open', 'Close']].min(axis=1) - df['Low']) / df['Close']
    df['Body_Pct'] = abs(df['Open'] - df['Close']) / df['Close']
    
    # 7. Calendar Features
    if isinstance(df.index, pd.DatetimeIndex):
        df['DayOfWeek'] = df.index.dayofweek
        df['Month'] = df.index.month
        df['Quarter'] = df.index.quarter
        df['Is_Month_End'] = df.index.is_month_end.astype(int)
        df['Is_Month_Start'] = df.index.is_month_start.astype(int)
        
    return df.dropna()
