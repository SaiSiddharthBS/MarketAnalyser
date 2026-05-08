"""
Agent Alpha v2.0 — Historical Crisis Stress Tester
===================================================
Simulates how the current portfolio would perform if a historical 
black swan event occurred tomorrow.

Institutional risk management isn't just about VaR (Value at Risk) in 
normal times; it's about survival during non-normal distributions.

Historical Scenarios modeled:
1. 2008 Global Financial Crisis (Lehman collapse)
2. 2020 COVID-19 Flash Crash
3. 2013 Taper Tantrum (India-specific liquidity crisis)
4. 2016 Demonetisation (India-specific systemic shock)
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    from data.stock_fetcher import download_ohlcv
except ImportError:
    download_ohlcv = None

# Defining historical crisis dates (Format: Start Date, Peak Trough Date, Recovery Date)
CRISIS_SCENARIOS = {
    "GFC_2008": {
        "name": "2008 Global Financial Crisis",
        "start": "2008-01-01",
        "trough": "2008-10-27", 
        "end": "2009-05-31",
        "nifty_drawdown": -59.5,
    },
    "COVID_2020": {
        "name": "2020 COVID-19 Crash",
        "start": "2020-02-19",
        "trough": "2020-03-23",
        "end": "2020-10-31",
        "nifty_drawdown": -39.3,
    },
    "TAPER_TANTRUM_2013": {
        "name": "2013 Taper Tantrum (INR Crisis)",
        "start": "2013-05-22",
        "trough": "2013-08-28",
        "end": "2014-03-31",
        "nifty_drawdown": -12.5,
    },
    "DEMONETISATION_2016": {
        "name": "2016 Demonetisation",
        "start": "2016-11-08",
        "trough": "2016-12-26",
        "end": "2017-03-31",
        "nifty_drawdown": -9.2,
    }
}

class StressTester:
    """Simulates portfolio performance across historical shocks."""

    def __init__(self):
        # Cache for historical index returns
        self.index_returns_cache = {}

    def _get_benchmark_returns(self, ticker: str = "^NSEI") -> pd.Series:
        """Fetch and cache benchmark returns for crisis alignment."""
        if ticker in self.index_returns_cache:
            return self.index_returns_cache[ticker]
            
        if download_ohlcv is not None:
            # We need deep history for 2008
            df = download_ohlcv(ticker, period="max")
            if df is not None and not df.empty:
                returns = df["Close"].pct_change().dropna()
                self.index_returns_cache[ticker] = returns
                return returns
                
        return pd.Series(dtype=float)

    def calculate_beta_to_benchmark(self, stock_returns: pd.Series, bench_returns: pd.Series) -> float:
        """Calculate historical Beta of stock to benchmark."""
        # Align dates
        aligned = pd.concat([stock_returns, bench_returns], axis=1, join="inner").dropna()
        if len(aligned) < 60:
            return 1.0 # Default to market beta
            
        stock_col, bench_col = aligned.columns[0], aligned.columns[1]
        
        covariance = np.cov(aligned[stock_col], aligned[bench_col])[0][1]
        variance = np.var(aligned[bench_col])
        
        if variance == 0:
            return 1.0
            
        beta = covariance / variance
        
        # Cap unreasonable betas
        return max(0.1, min(3.0, beta))

    def run_stress_test(
        self, 
        portfolio_holdings: Dict[str, float], 
        stock_returns_history: Dict[str, pd.Series],
        max_allowed_drawdown: float = 20.0
    ) -> Dict[str, Any]:
        """
        Run stress test on current portfolio.
        
        Args:
            portfolio_holdings: Dict of symbol -> weight (summing to 1.0)
            stock_returns_history: Dict of symbol -> full historical return series
            max_allowed_drawdown: Threshold above which deleveraging is recommended
            
        Returns:
            Dict containing simulated drawdowns and risk assessment.
        """
        if not portfolio_holdings:
            return {"status": "NO_PORTFOLIO", "message": "No holdings to stress test"}
            
        bench_returns = self._get_benchmark_returns()
        
        # 1. Calculate current Beta profile for the portfolio
        stock_betas = {}
        for symbol, returns in stock_returns_history.items():
            if symbol in portfolio_holdings:
                beta = self.calculate_beta_to_benchmark(returns, bench_returns)
                stock_betas[symbol] = beta
                
        portfolio_beta = sum(weight * stock_betas.get(symbol, 1.0) 
                             for symbol, weight in portfolio_holdings.items())

        # 2. Simulate Crisis Scenarios
        scenario_results = {}
        worst_scenario_drawdown = 0.0
        worst_scenario_name = ""
        
        for scenario_id, details in CRISIS_SCENARIOS.items():
            # Method 1: Actual Historical Performance (if stock existed)
            # Method 2: Beta-adjusted market performance (if stock is new)
            
            simulated_drawdown = 0.0
            stocks_with_history = 0
            
            for symbol, weight in portfolio_holdings.items():
                returns = stock_returns_history.get(symbol)
                
                has_history = False
                stock_dd = 0.0
                
                if returns is not None and not returns.empty:
                    # Check if returns cover the crisis period
                    try:
                        start_date = pd.to_datetime(details["start"])
                        trough_date = pd.to_datetime(details["trough"])
                        
                        if start_date.tz_localize(None) >= returns.index[0].tz_localize(None):
                            # Calculate actual drawdown
                            crisis_slice = returns.loc[details["start"]:details["trough"]]
                            if len(crisis_slice) > 0:
                                comp_return = (1 + crisis_slice).prod() - 1
                                stock_dd = comp_return * 100
                                has_history = True
                    except Exception:
                        pass
                
                if not has_history:
                    # Beta approximation
                    beta = stock_betas.get(symbol, 1.0)
                    stock_dd = details["nifty_drawdown"] * beta
                    
                simulated_drawdown += weight * stock_dd
                if has_history:
                    stocks_with_history += 1
            
            scenario_results[scenario_id] = {
                "name": details["name"],
                "simulated_portfolio_drawdown": round(simulated_drawdown, 2),
                "benchmark_drawdown": details["nifty_drawdown"],
                "outperformance": round(simulated_drawdown - details["nifty_drawdown"], 2),
                "data_quality": f"{stocks_with_history}/{len(portfolio_holdings)} stocks had actual history"
            }
            
            if simulated_drawdown < worst_scenario_drawdown:
                worst_scenario_drawdown = simulated_drawdown
                worst_scenario_name = details["name"]

        # 3. Assess Risk Limits
        is_breaching = abs(worst_scenario_drawdown) > max_allowed_drawdown
        
        deleveraging_factor = 1.0
        if is_breaching:
            # How much do we need to cut exposure to survive?
            deleveraging_factor = max_allowed_drawdown / abs(worst_scenario_drawdown)
            
        return {
            "status": "COMPLETED",
            "portfolio_beta": round(portfolio_beta, 2),
            "worst_case_drawdown_pct": round(worst_scenario_drawdown, 2),
            "worst_case_scenario": worst_scenario_name,
            "max_allowed_drawdown_pct": max_allowed_drawdown,
            "breaching_limit": is_breaching,
            "recommended_deleveraging_factor": round(deleveraging_factor, 2),
            "scenarios": scenario_results,
            "date": datetime.now().strftime("%Y-%m-%d")
        }


# Global singleton
stress_tester = StressTester()
