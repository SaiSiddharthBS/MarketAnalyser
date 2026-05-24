import sys
import time
from arena.paper_trading import NIFTY_50_SYMBOLS
from data.stock_fetcher import download_ohlcv
from analysis.technical import get_technical_analysis
from analysis.ensemble import get_ensemble_analysis

print("Starting loop")
for symbol in NIFTY_50_SYMBOLS[:3]:
    print(f"Processing {symbol}")
    t0 = time.time()
    ticker = f"{symbol}.NS"
    df = download_ohlcv(ticker, period="6mo", interval="1d")
    print(f"  DL took {time.time()-t0:.2f}s")
    if df is None: continue
    
    t1 = time.time()
    tech = get_technical_analysis(symbol)
    print(f"  TA took {time.time()-t1:.2f}s")
    if not tech: continue
    
    t2 = time.time()
    ens = get_ensemble_analysis(symbol, df, "low_vol_chop")
    print(f"  Ens took {time.time()-t2:.2f}s")
