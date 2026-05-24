"""
Agent Alpha — Risk Parity & Volatility Engine
=============================================
Provides institutional-grade risk management by calculating:
1. Inverse Volatility Sizing (highly volatile stocks get smaller capital allocation)
2. Sector Concentration Limits (max 30% of portfolio per sector)
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Base NIFTY 50 annualized volatility is roughly 15-18% historically.
# We will use 20% as our "baseline" annualized volatility.
BASELINE_ANNUAL_VOL = 0.20

def calculate_volatility_scalar(symbol: str, df: pd.DataFrame) -> float:
    """
    Calculates an inverse-volatility multiplier.
    If a stock is twice as volatile as the baseline, its position size is cut in half.
    If a stock is very stable, it gets its full allocation (capped at 1.2x).
    """
    if df is None or len(df) < 20:
        return 1.0  # Fallback
        
    try:
        # Calculate daily returns
        returns = df["Close"].pct_change().dropna()
        
        # Calculate annualized volatility (standard deviation of daily returns * sqrt(252))
        annualized_vol = returns.std() * np.sqrt(252)
        
        if isinstance(annualized_vol, pd.Series):
            annualized_vol = annualized_vol.iloc[0]
            
        if annualized_vol == 0 or pd.isna(annualized_vol):
            return 1.0
            
        # Inverse Volatility Scalar
        # Target Vol / Actual Vol
        scalar = BASELINE_ANNUAL_VOL / annualized_vol
        
        # Cap the multiplier so we don't massively over-allocate to "dead" stocks
        # and floor it so we don't allocate practically nothing to high-vol stocks
        scalar = np.clip(scalar, 0.25, 1.2)
        
        return round(float(scalar), 2)
        
    except Exception as e:
        logger.error(f"Failed to calculate vol scalar for {symbol}: {e}")
        return 1.0

_SECTOR_CACHE = {}

def check_sector_concentration(sector: str, open_positions: List[Dict[str, Any]], total_capital: float, max_sector_pct: float = 0.30) -> Dict[str, Any]:
    """
    Ensures that adding a new trade in the given sector will not exceed
    the maximum sector concentration limit (e.g., 30% of total capital).
    """
    if not sector or sector == "Unknown":
        return {"approved": True, "current_exposure_pct": 0.0}
        
    try:
        sector_invested = 0.0
        
        for pos in open_positions:
            pos_sector = pos.get("sector")
            if not pos_sector:
                symbol = pos.get("symbol")
                if symbol:
                    if symbol in _SECTOR_CACHE:
                        pos_sector = _SECTOR_CACHE[symbol]
                    else:
                        try:
                            import yfinance as yf
                            pos_sector = yf.Ticker(f"{symbol}.NS").info.get("sector", "Unknown")
                            _SECTOR_CACHE[symbol] = pos_sector
                        except:
                            pos_sector = "Unknown"
                            _SECTOR_CACHE[symbol] = "Unknown"
                else:
                    pos_sector = "Unknown"
                    
            if pos_sector == sector:
                # Add position value (use quantity * price if invested_amount isn't directly available)
                # But typically we use position_value or (quantity * entry_price)
                val = float(pos.get("position_value", 0))
                if val == 0:
                    val = float(pos.get("quantity", 0)) * float(pos.get("entry_price", 0))
                sector_invested += val
                
        current_exposure_pct = sector_invested / total_capital if total_capital > 0 else 0
        
        if current_exposure_pct >= max_sector_pct:
            return {
                "approved": False,
                "current_exposure_pct": round(current_exposure_pct, 3),
                "reason": f"Sector '{sector}' exposure is {current_exposure_pct*100:.1f}%, exceeding max limit of {max_sector_pct*100:.1f}%"
            }
            
        return {
            "approved": True,
            "current_exposure_pct": round(current_exposure_pct, 3),
            "reason": "Concentration OK"
        }
    except Exception as e:
        logger.error(f"Failed to calculate sector concentration for {sector}: {e}")
        return {"approved": True, "current_exposure_pct": 0.0}

if __name__ == "__main__":
    # Quick test
    import yfinance as yf
    df = yf.download("ADANIENT.NS", period="3mo", progress=False)
    vol_scalar = calculate_volatility_scalar("ADANIENT.NS", df)
    print(f"ADANIENT.NS Volatility Scalar: {vol_scalar}")
    
    df_hdfc = yf.download("HDFCBANK.NS", period="3mo", progress=False)
    vol_scalar_hdfc = calculate_volatility_scalar("HDFCBANK.NS", df_hdfc)
    print(f"HDFCBANK.NS Volatility Scalar: {vol_scalar_hdfc}")
