import yfinance as yf
import pandas as pd
from typing import Dict, Any, Tuple
import datetime

class MacroSentinel:
    """
    Antigravity Module 1: Cross-Asset Macro Filter
    The external environment check. Global forces override domestic signals.
    """
    
    def __init__(self):
        self.tickers = {
            "usd_inr": "INR=X",
            "brent_crude": "BZ=F",
            "sp500": "ES=F",
            "gold": "GC=F",
            "us_10y": "^TNX"
        }
        self._cached_score = None
        self._last_fetch_time = None
        
    def fetch_macro_data(self) -> Dict[str, pd.DataFrame]:
        data = {}
        for key, ticker in self.tickers.items():
            try:
                # Fetch last 10 days to calculate momentum/changes
                df = yf.download(ticker, period="10d", progress=False)
                if not df.empty:
                    data[key] = df
            except Exception as e:
                print(f"Failed to fetch {key}: {e}")
        return data

    def calculate_macro_score(self) -> Dict[str, Any]:
        now = datetime.datetime.now()
        if self._cached_score and self._last_fetch_time:
            if (now - self._last_fetch_time).total_seconds() < 300: # 5 minutes cache
                return self._cached_score

        data = self.fetch_macro_data()
        
        votes = {
            "usd_inr": {"vote": 0, "weight": 0.30, "value": 0},
            "brent_crude": {"vote": 0, "weight": 0.25, "value": 0},
            "sp500": {"vote": 0, "weight": 0.25, "value": 0},
            "gold": {"vote": 0, "weight": 0.10, "value": 0},
            "us_10y": {"vote": 0, "weight": 0.10, "value": 0}
        }
        
        # 1. USD/INR (Weight 30%)
        if "usd_inr" in data:
            df = data["usd_inr"]["Close"].squeeze()
            current = float(df.iloc[-1])
            votes["usd_inr"]["value"] = round(current, 2)
            if current < 84.50:
                votes["usd_inr"]["vote"] = 1
            elif current > 85.50:
                votes["usd_inr"]["vote"] = -1
                
        # 2. Brent Crude (Weight 25%)
        if "brent_crude" in data:
            df = data["brent_crude"]["Close"].squeeze()
            current = float(df.iloc[-1])
            past_5d = float(df.iloc[-5]) if len(df) >= 5 else current
            pct_change = (current - past_5d) / past_5d * 100
            votes["brent_crude"]["value"] = round(current, 2)
            
            if current < 85.0:
                votes["brent_crude"]["vote"] = 1
            elif current > 95.0 or pct_change > 5.0:
                votes["brent_crude"]["vote"] = -1
                
        # 3. S&P 500 Futures (Weight 25%)
        if "sp500" in data:
            df = data["sp500"]["Close"].squeeze()
            current = float(df.iloc[-1])
            past_1d = float(df.iloc[-2]) if len(df) >= 2 else current
            pct_change = (current - past_1d) / past_1d * 100
            votes["sp500"]["value"] = f"{round(pct_change, 2)}%"
            
            if pct_change >= 0:
                votes["sp500"]["vote"] = 1
            elif pct_change < -0.8:
                votes["sp500"]["vote"] = -1
                
        # 4. Gold (Weight 10%)
        if "gold" in data:
            df = data["gold"]["Close"].squeeze()
            current = float(df.iloc[-1])
            past_3d = float(df.iloc[-3]) if len(df) >= 3 else current
            pct_change = (current - past_3d) / past_3d * 100
            votes["gold"]["value"] = f"{round(pct_change, 2)}%"
            
            if pct_change <= 0:
                votes["gold"]["vote"] = 1
            elif pct_change > 1.5:
                votes["gold"]["vote"] = -1
                
        # 5. US 10Y Yield (Weight 10%)
        if "us_10y" in data:
            df = data["us_10y"]["Close"].squeeze()
            current = float(df.iloc[-1])
            past_5d = float(df.iloc[-5]) if len(df) >= 5 else current
            bps_change = (current - past_5d) * 100 # 1% = 100 bps
            votes["us_10y"]["value"] = round(current, 3)
            
            if bps_change <= 0:
                votes["us_10y"]["vote"] = 1
            elif bps_change > 20:
                votes["us_10y"]["vote"] = -1

        # Calculate Final Score
        macro_score = sum(v["vote"] * v["weight"] for v in votes.values())
        macro_score = round(macro_score, 2)
        
        status = "CLEAR"
        if macro_score < -0.60:
            status = "FULL MACRO VETO"
        elif macro_score < -0.30:
            status = "MACRO VETO"
        elif macro_score > 0.20:
            status = "MACRO TAILWIND"

        def map_vote_to_string(vote: int) -> str:
            return "Bullish" if vote == 1 else "Bearish" if vote == -1 else "Neutral"

        result = {
            "score": macro_score,
            "status": status,
            "breakdown": {
                "USD/INR": {"signal": map_vote_to_string(votes["usd_inr"]["vote"]), "val": votes["usd_inr"]["value"]},
                "Brent Crude": {"signal": map_vote_to_string(votes["brent_crude"]["vote"]), "val": votes["brent_crude"]["value"]},
                "S&P 500 Futures": {"signal": map_vote_to_string(votes["sp500"]["vote"]), "val": votes["sp500"]["value"]},
                "Gold": {"signal": map_vote_to_string(votes["gold"]["vote"]), "val": votes["gold"]["value"]},
                "US 10Y Yield": {"signal": map_vote_to_string(votes["us_10y"]["vote"]), "val": votes["us_10y"]["value"]}
            }
        }
        
        self._cached_score = result
        self._last_fetch_time = now
        return result

# Singleton instance for easy access
macro_engine = MacroSentinel()

def get_macro_environment():
    return macro_engine.calculate_macro_score()
