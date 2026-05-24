import pandas as pd
import numpy as np
import logging
import yfinance as yf

logger = logging.getLogger(__name__)

def get_volume_profile(ticker: str, period: str = "5d", interval: str = "5m", bins: int = 50) -> dict:
    """
    Calculates the Volume Point of Control (VPOC) and identifies institutional order blocks.
    Uses 5m intraday data to accurately capture block trades.
    """
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        if df.empty or 'Volume' not in df.columns:
            return {"vpoc": None, "order_blocks": [], "accumulation_score": 0}
            
        # Convert to 1D arrays
        close = df['Close'].values.flatten()
        volume = df['Volume'].values.flatten()
        
        # Create price bins
        min_price = np.min(close)
        max_price = np.max(close)
        
        if min_price == max_price:
            return {"vpoc": min_price, "order_blocks": [], "accumulation_score": 0}
            
        # Compute volume profile
        price_bins = np.linspace(min_price, max_price, bins)
        vol_profile = np.zeros(bins)
        
        for i in range(len(close)):
            idx = np.abs(price_bins - close[i]).argmin()
            vol_profile[idx] += volume[i]
            
        # Volume Point of Control (VPOC)
        vpoc_idx = np.argmax(vol_profile)
        vpoc_price = price_bins[vpoc_idx]
        
        # Identify massive volume spikes (Dark Pool / Block Trade proxies)
        avg_vol = np.mean(volume)
        vol_std = np.std(volume)
        
        spike_indices = np.where(volume > (avg_vol + 3 * vol_std))[0]
        
        order_blocks = []
        for idx in spike_indices:
            # Determine if it's buying or selling pressure based on close vs open
            bar_open = float(df['Open'].iloc[idx].iloc[0]) if isinstance(df['Open'].iloc[idx], pd.Series) else float(df['Open'].iloc[idx])
            bar_close = float(df['Close'].iloc[idx].iloc[0]) if isinstance(df['Close'].iloc[idx], pd.Series) else float(df['Close'].iloc[idx])
            
            if bar_close > bar_open:
                order_type = "DEMAND" # Institutional Buy
            else:
                order_type = "SUPPLY" # Institutional Sell
                
            order_blocks.append({
                "price": round(bar_close, 2),
                "volume": float(volume[idx]),
                "type": order_type,
                "timestamp": str(df.index[idx])
            })
            
        # Accumulation score: How many DEMAND blocks vs SUPPLY blocks
        demand_vol = sum(ob['volume'] for ob in order_blocks if ob['type'] == 'DEMAND')
        supply_vol = sum(ob['volume'] for ob in order_blocks if ob['type'] == 'SUPPLY')
        
        total_block_vol = demand_vol + supply_vol
        accumulation_score = ((demand_vol - supply_vol) / total_block_vol * 100) if total_block_vol > 0 else 0
        
        return {
            "vpoc": round(float(vpoc_price), 2),
            "order_blocks": order_blocks,
            "accumulation_score": round(float(accumulation_score), 2), # -100 to 100
            "current_price": round(float(close[-1]), 2)
        }
    except Exception as e:
        logger.error(f"Smart Money extraction failed for {ticker}: {e}")
        return {"vpoc": None, "order_blocks": [], "accumulation_score": 0}

def check_smart_money_signal(ticker: str) -> dict:
    """Returns a quantitative signal based on institutional footprint."""
    smc = get_volume_profile(ticker)
    if smc["vpoc"] is None:
        return {"signal": "NEUTRAL", "confidence": 0}
        
    price = smc["current_price"]
    vpoc = smc["vpoc"]
    score = smc["accumulation_score"]
    
    # VPOC acts as institutional gravity.
    # If price is slightly above VPOC + high accumulation, it's a breakout.
    # If price is at VPOC + high accumulation, it's institutional absorption (strong buy).
    
    if score > 30 and price >= vpoc:
        return {"signal": "STRONG_BUY", "confidence": min(100, 50 + score)}
    elif score > 15 and price >= vpoc * 0.98:
        return {"signal": "BUY", "confidence": min(100, 30 + score)}
    elif score < -30 and price <= vpoc:
        return {"signal": "STRONG_SELL", "confidence": min(100, 50 + abs(score))}
    elif score < -15 and price <= vpoc * 1.02:
        return {"signal": "SELL", "confidence": min(100, 30 + abs(score))}
        
    return {"signal": "NEUTRAL", "confidence": 0, "smc_data": smc}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(check_smart_money_signal("RELIANCE.NS"))
