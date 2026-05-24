import pandas as pd
import numpy as np
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

try:
    from data.stock_fetcher import download_ohlcv
except ImportError:
    # Fallback for standalone testing
    import yfinance as yf
    def download_ohlcv(symbol: str, start="2020-01-01", end=None):
        return yf.download(symbol, start=start, end=end, progress=False)

# Pre-defined known correlated pairs in NIFTY 50
KNOWN_PAIRS = [
    ("HDFCBANK.NS", "ICICIBANK.NS"),
    ("TCS.NS", "INFY.NS"),
    ("RELIANCE.NS", "ONGC.NS"),
    ("TATAMOTORS.NS", "M&M.NS"),
    ("JSWSTEEL.NS", "TATASTEEL.NS"),
    ("HINDUNILVR.NS", "ITC.NS"),
    ("AXISBANK.NS", "SBIN.NS")
]

def analyze_pairs(z_score_threshold: float = 2.0) -> List[Dict]:
    """
    Downloads data for known pairs and checks if their spread has diverged beyond the z-score threshold.
    Returns a list of trade signals (Long the undervalued, Short the overvalued).
    """
    signals = []
    
    for asset1, asset2 in KNOWN_PAIRS:
        try:
            df1 = download_ohlcv(asset1, start="2024-01-01")
            df2 = download_ohlcv(asset2, start="2024-01-01")
            
            if df1 is None or df2 is None or df1.empty or df2.empty:
                continue
                
            # Align dates
            df1 = df1['Close'].dropna()
            df2 = df2['Close'].dropna()
            
            data = pd.concat([df1, df2], axis=1, join='inner')
            data.columns = [asset1, asset2]
            
            # Simple spread calculation: log price ratio
            data['spread'] = np.log(data[asset1]) - np.log(data[asset2])
            
            # Rolling 60-day mean and std dev
            data['mean_spread'] = data['spread'].rolling(window=60).mean()
            data['std_spread'] = data['spread'].rolling(window=60).std()
            
            # Z-Score
            data['z_score'] = (data['spread'] - data['mean_spread']) / data['std_spread']
            
            current_z = float(data['z_score'].iloc[-1])
            
            if current_z > z_score_threshold:
                # Spread is too high -> asset1 is overvalued relative to asset2
                # Action: Short Asset1, Long Asset2
                signals.append({
                    "symbol": asset1.replace(".NS", ""),
                    "signal": "STRONG_SELL",
                    "confidence": min(100, 50 + (current_z - 2) * 20),
                    "reason": f"StatArb: Overvalued vs {asset2.replace('.NS', '')} (Z: {current_z:.2f})"
                })
                signals.append({
                    "symbol": asset2.replace(".NS", ""),
                    "signal": "STRONG_BUY",
                    "confidence": min(100, 50 + (current_z - 2) * 20),
                    "reason": f"StatArb: Undervalued vs {asset1.replace('.NS', '')} (Z: {current_z:.2f})"
                })
            elif current_z < -z_score_threshold:
                # Spread is too low -> asset1 is undervalued relative to asset2
                # Action: Long Asset1, Short Asset2
                signals.append({
                    "symbol": asset1.replace(".NS", ""),
                    "signal": "STRONG_BUY",
                    "confidence": min(100, 50 + (abs(current_z) - 2) * 20),
                    "reason": f"StatArb: Undervalued vs {asset2.replace('.NS', '')} (Z: {current_z:.2f})"
                })
                signals.append({
                    "symbol": asset2.replace(".NS", ""),
                    "signal": "STRONG_SELL",
                    "confidence": min(100, 50 + (abs(current_z) - 2) * 20),
                    "reason": f"StatArb: Overvalued vs {asset1.replace('.NS', '')} (Z: {current_z:.2f})"
                })
                
        except Exception as e:
            logger.error(f"Failed to analyze pair {asset1}-{asset2}: {e}")
            
    return signals

def get_stat_arb_signal(ticker: str) -> dict:
    """Returns the stat arb signal for a specific ticker if one exists."""
    signals = analyze_pairs()
    for s in signals:
        if s["symbol"] == ticker:
            return {"signal": s["signal"], "confidence": s["confidence"]}
    return {"signal": "NEUTRAL", "confidence": 0}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(analyze_pairs())
