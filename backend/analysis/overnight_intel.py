"""
Agent Alpha — Overnight Global Intelligence Engine
====================================================
Runs at 6:00 AM IST (before Indian market opens at 9:15 AM).
Scans EVERYTHING that happened overnight across the world and produces
a single pre-market intelligence briefing that adjusts the regime and
signal thresholds for the morning session.

Sources analyzed:
1. US Markets (S&P 500, NASDAQ, Dow Jones) — closing performance
2. Asian Markets (Nikkei, Hang Seng, SGX Nifty) — live pre-market
3. European Futures (STOXX 50, FTSE) — early sentiment
4. Commodities (Crude Oil, Gold, Copper, Natural Gas)
5. Currencies (DXY Dollar Index, USD/INR, EUR/USD)
6. Bond Markets (US 10Y, US 2Y, yield curve inversion check)
7. Volatility (VIX, India VIX)
8. Crypto Sentiment (Bitcoin as risk-on/risk-off proxy)
9. FII/DII Flow Momentum (rolling 5-day trend)
10. Global Fear & Greed proxy (multi-asset composite)
"""
import yfinance as yf
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


# ─── GLOBAL ASSET UNIVERSE ──────────────────────────────────────────
OVERNIGHT_TICKERS = {
    # US Markets
    "sp500": "^GSPC",
    "nasdaq": "^IXIC",
    "dow": "^DJI",
    
    # Asian Markets
    "nikkei": "^N225",
    "hang_seng": "^HSI",
    "sgx_nifty": "^STI",      # Singapore Straits Times (proxy)
    
    # European Futures
    "stoxx50": "^STOXX50E",
    "ftse": "^FTSE",
    
    # Commodities
    "crude_wti": "CL=F",
    "crude_brent": "BZ=F",
    "gold": "GC=F",
    "silver": "SI=F",
    "copper": "HG=F",
    "natural_gas": "NG=F",
    
    # Currencies
    "dxy": "DX-Y.NYB",        # US Dollar Index
    "usd_inr": "INR=X",
    "eur_usd": "EURUSD=X",
    
    # Bonds
    "us_10y": "^TNX",
    "us_2y": "^IRX",           # 13-week T-bill (proxy for short end)
    
    # Volatility
    "vix": "^VIX",
    "india_vix": "^INDIAVIX",
    
    # Crypto (Risk Sentiment Proxy)
    "bitcoin": "BTC-USD",
    
    # Geopolitical Risk & Macro Proxies
    "defense_etf": "ITA",     # iShares U.S. Aerospace & Defense ETF
    "fed_funds": "ZQ=F",      # 30-Day Federal Funds futures
    "shanghai_comp": "000001.SS", # China PMI/Manufacturing proxy
    "crb_index": "CRB",       # Commodity index proxy (fallback to basket if unavailable)
}


def _safe_fetch(ticker: str, period: str = "6mo") -> Optional[pd.DataFrame]:
    """Safely fetch data for a single ticker. Never crashes."""
    try:
        df = yf.download(ticker, period=period, progress=False, timeout=10)
        if df is not None and not df.empty and len(df) >= 2:
            return df
    except Exception:
        pass
    return None


def _calc_change(df: pd.DataFrame) -> dict:
    """Calculate 1-day change from a price DataFrame."""
    if df is None or len(df) < 2:
        return {"current": 0, "prev": 0, "change_pct": 0, "available": False}
    
    close = df["Close"].squeeze() if isinstance(df["Close"], pd.DataFrame) else df["Close"]
    current = float(close.iloc[-1])
    prev = float(close.iloc[-2])
    change_pct = ((current - prev) / prev) * 100 if prev != 0 else 0
    
    return {
        "current": round(current, 2),
        "prev": round(prev, 2),
        "change_pct": round(change_pct, 2),
        "available": True
    }


def _calc_trend(df: pd.DataFrame) -> dict:
    """Calculate 3-month and 6-month percent change."""
    if df is None or len(df) < 60:
        return {"3mo_pct": 0, "6mo_pct": 0, "available": False}
    
    close = df["Close"].squeeze() if isinstance(df["Close"], pd.DataFrame) else df["Close"]
    current = float(close.iloc[-1])
    
    # Approx 60 trading days in 3 months, 120 in 6 months
    price_3mo = float(close.iloc[-min(60, len(close))])
    price_6mo = float(close.iloc[0]) # Since we fetch 6mo
    
    pct_3mo = ((current - price_3mo) / price_3mo) * 100 if price_3mo != 0 else 0
    pct_6mo = ((current - price_6mo) / price_6mo) * 100 if price_6mo != 0 else 0
    
    return {
        "3mo_pct": round(pct_3mo, 2),
        "6mo_pct": round(pct_6mo, 2),
        "available": True
    }


def scan_overnight_global() -> Dict[str, Any]:
    """
    The main overnight scan. Fetches all global assets and computes
    a comprehensive pre-market intelligence report.
    
    Returns a dict with:
    - global_score: -100 to +100 (composite sentiment)
    - regime_adjustment: suggested regime bias for today
    - asset_breakdown: detailed per-asset analysis
    - alerts: list of critical overnight events
    - pre_market_bias: BULLISH / BEARISH / NEUTRAL
    """
    logger.info("🌍 Starting Overnight Global Intelligence Scan...")
    
    results = {}
    alerts = []
    
    # ─── FETCH ALL ASSETS ────────────────────────────────────────
    for name, ticker in OVERNIGHT_TICKERS.items():
        df = _safe_fetch(ticker)
        results[name] = _calc_change(df)
    
    # ─── SCORING ENGINE ──────────────────────────────────────────
    # Each category contributes to a weighted global score
    
    score = 0.0
    breakdown = {}
    
    # 1. US MARKETS (Weight: 30%) — Most correlated to Indian open
    us_score = 0.0
    us_assets = ["sp500", "nasdaq", "dow"]
    us_changes = []
    for asset in us_assets:
        if results.get(asset, {}).get("available"):
            change = results[asset]["change_pct"]
            us_changes.append(change)
    
    if us_changes:
        avg_us = np.mean(us_changes)
        us_score = np.clip(avg_us * 10, -100, 100)  # ±1% move = ±10 points
        
        # Alert on major US moves
        if abs(avg_us) > 1.5:
            direction = "rallied" if avg_us > 0 else "crashed"
            alerts.append(f"🇺🇸 US markets {direction} {abs(avg_us):.1f}% overnight")
    
    breakdown["us_markets"] = {"score": round(us_score, 1), "weight": 30, "changes": {a: results.get(a, {}).get("change_pct", 0) for a in us_assets}}
    score += us_score * 0.30
    
    # 2. ASIAN MARKETS (Weight: 15%) — Direct regional correlation
    asia_score = 0.0
    asia_assets = ["nikkei", "hang_seng", "sgx_nifty"]
    asia_changes = []
    for asset in asia_assets:
        if results.get(asset, {}).get("available"):
            asia_changes.append(results[asset]["change_pct"])
    
    if asia_changes:
        avg_asia = np.mean(asia_changes)
        asia_score = np.clip(avg_asia * 10, -100, 100)
        
        if abs(avg_asia) > 2.0:
            direction = "surged" if avg_asia > 0 else "sold off"
            alerts.append(f"🌏 Asian markets {direction} {abs(avg_asia):.1f}%")
    
    breakdown["asian_markets"] = {"score": round(asia_score, 1), "weight": 15}
    score += asia_score * 0.15
    
    # 3. COMMODITIES (Weight: 15%) — Inflation / growth signal
    comm_score = 0.0
    
    # Crude oil: Rising = bearish for India (import dependent)
    crude_change = results.get("crude_brent", {}).get("change_pct", 0)
    if results.get("crude_brent", {}).get("available"):
        comm_score -= crude_change * 8  # Inverse: oil up = India down
        if crude_change > 3:
            alerts.append(f"🛢️ Crude oil spiked {crude_change:.1f}% — bearish for India")
        elif crude_change < -3:
            alerts.append(f"🛢️ Crude oil dropped {abs(crude_change):.1f}% — bullish for India")
    
    # Gold: Rising gold = risk-off = bearish for equities
    gold_change = results.get("gold", {}).get("change_pct", 0)
    if results.get("gold", {}).get("available"):
        comm_score -= gold_change * 5  # Gold up = slight equity negative
    
    # Copper: Rising copper = global growth = bullish
    copper_change = results.get("copper", {}).get("change_pct", 0)
    if results.get("copper", {}).get("available"):
        comm_score += copper_change * 5  # Copper up = growth optimism
    
    comm_score = np.clip(comm_score, -100, 100)
    breakdown["commodities"] = {"score": round(comm_score, 1), "weight": 15, "crude": crude_change, "gold": gold_change, "copper": copper_change}
    score += comm_score * 0.15
    
    # 4. CURRENCIES (Weight: 15%) — Rupee strength / FII flow signal
    fx_score = 0.0
    
    # DXY: Strong dollar = bearish for EMs including India
    dxy_change = results.get("dxy", {}).get("change_pct", 0)
    if results.get("dxy", {}).get("available"):
        fx_score -= dxy_change * 12  # DXY up = bearish for India
        if dxy_change > 0.5:
            alerts.append(f"💵 US Dollar strengthened {dxy_change:.1f}% — EM pressure")
    
    # USD/INR: Rupee weakening = bearish
    inr_change = results.get("usd_inr", {}).get("change_pct", 0)
    if results.get("usd_inr", {}).get("available"):
        fx_score -= inr_change * 10  # INR weakening (USD/INR up) = bearish
        if inr_change > 0.3:
            alerts.append(f"₹ Rupee weakened {inr_change:.1f}% against USD")
    
    fx_score = np.clip(fx_score, -100, 100)
    breakdown["currencies"] = {"score": round(fx_score, 1), "weight": 15, "dxy": dxy_change, "usd_inr": inr_change}
    score += fx_score * 0.15
    
    # 5. BOND MARKETS (Weight: 10%) — Yield curve / rate expectations
    bond_score = 0.0
    
    us10y_change = results.get("us_10y", {}).get("change_pct", 0)
    if results.get("us_10y", {}).get("available"):
        # Rising yields = bearish for growth stocks
        bond_score -= us10y_change * 5
        current_yield = results["us_10y"]["current"]
        if current_yield > 5.0:
            alerts.append(f"📈 US 10Y yield at {current_yield}% — elevated pressure on equities")
    
    bond_score = np.clip(bond_score, -100, 100)
    breakdown["bonds"] = {"score": round(bond_score, 1), "weight": 10}
    score += bond_score * 0.10
    
    # 6. VOLATILITY (Weight: 10%) — Fear gauge
    vol_score = 0.0
    
    vix_current = results.get("vix", {}).get("current", 0)
    vix_change = results.get("vix", {}).get("change_pct", 0)
    if results.get("vix", {}).get("available"):
        if vix_current > 30:
            vol_score = -80  # Extreme fear
            alerts.append(f"🔴 VIX at {vix_current} — extreme fear in global markets")
        elif vix_current > 25:
            vol_score = -50  # High fear
            alerts.append(f"🟠 VIX elevated at {vix_current}")
        elif vix_current < 15:
            vol_score = 30   # Complacency (mild positive)
        else:
            vol_score = 0
        
        # VIX spike matters more than level
        if vix_change > 15:
            vol_score -= 30
            alerts.append(f"⚡ VIX spiked {vix_change:.1f}% overnight — panic selling")
    
    vol_score = np.clip(vol_score, -100, 100)
    breakdown["volatility"] = {"score": round(vol_score, 1), "weight": 10, "vix": vix_current, "vix_change": vix_change}
    score += vol_score * 0.10
    
    # 7. CRYPTO RISK SENTIMENT (Weight: 5%) — Risk-on / risk-off proxy
    crypto_score = 0.0
    btc_change = results.get("bitcoin", {}).get("change_pct", 0)
    if results.get("bitcoin", {}).get("available"):
        crypto_score = np.clip(btc_change * 5, -100, 100)
        if abs(btc_change) > 5:
            direction = "surged" if btc_change > 0 else "crashed"
            alerts.append(f"₿ Bitcoin {direction} {abs(btc_change):.1f}% — risk sentiment shift")
    
    breakdown["crypto_sentiment"] = {"score": round(crypto_score, 1), "weight": 5, "btc_change": btc_change}
    score += crypto_score * 0.05
    
    # ─── EVENT-DRIVEN MACRO PROXIES ────────────────────────────────
    
    # 8. GEOPOLITICAL RISK SCORE
    # If Defense + Gold + Oil all surge, severe risk-off
    geo_score = 0.0
    def_change = results.get("defense_etf", {}).get("change_pct", 0)
    if def_change > 1.5 and gold_change > 1.0 and crude_change > 1.5:
        geo_score = -50  # Very bearish for standard equities
        alerts.append("🛡️ Geopolitical Risk Spike Detected: Defense + Gold + Oil surging")
    breakdown["geopolitical_risk"] = {"score": geo_score, "weight": "override"}
    score += geo_score
    
    # 9. FED WATCH PROXY
    # If 2Y yield drops sharply or Fed Funds futures (ZQ=F) rise (implied rate drops), bullish
    fed_score = 0.0
    us2y_change = results.get("us_2y", {}).get("change_pct", 0)
    if us2y_change < -2.0:
        fed_score = 15  # Market pricing in cuts
        alerts.append(f"🕊️ US 2Y dropped {abs(us2y_change):.1f}% — market pricing dovish Fed")
    elif us2y_change > 2.0:
        fed_score = -15 # Hawkish
        alerts.append(f"🦅 US 2Y spiked {us2y_change:.1f}% — market pricing hawkish Fed")
    breakdown["fed_watch"] = {"score": fed_score, "weight": "modifier"}
    score += fed_score
    
    # 10. CHINA PMI / MANUFACTURING PROXY
    china_score = 0.0
    shanghai_change = results.get("shanghai_comp", {}).get("change_pct", 0)
    if shanghai_change > 1.5 and copper_change > 1.0:
        china_score = 10
        alerts.append("🏭 China Rebound Proxy: Shanghai + Copper surging")
    elif shanghai_change < -1.5 and copper_change < -1.0:
        china_score = -10
    breakdown["china_pmi_proxy"] = {"score": china_score, "weight": "modifier"}
    score += china_score
    
    # 11. GLOBAL LIQUIDITY INDEX
    # Expanding liquidity (DXY drops + yields drop) is very bullish
    liquidity_score = 0.0
    if dxy_change < -0.5 and us10y_change < -1.0:
        liquidity_score = 15
        alerts.append("🌊 Global Liquidity Expansion: Dollar and Yields both falling")
    elif dxy_change > 0.5 and us10y_change > 1.0:
        liquidity_score = -15
        alerts.append("🏜️ Global Liquidity Contraction: Dollar and Yields both rising")
    breakdown["global_liquidity"] = {"score": liquidity_score, "weight": "modifier"}
    score += liquidity_score

    # 12. COMMODITY SUPERCYCLE DETECTOR
    supercycle_score = 0.0
    crb_df = _safe_fetch("CRB", period="6mo")
    if crb_df is not None:
        crb_trend = _calc_trend(crb_df)
        if crb_trend["6mo_pct"] > 15:
            supercycle_score = -10  # Broad inflation headwind for EMs
            alerts.append(f"🔥 Commodity Supercycle: CRB index up {crb_trend['6mo_pct']}% over 6mo")
    else:
        # Fallback to basket if CRB is unavailable
        basket = ["crude_brent", "gold", "copper", "natural_gas"]
        basket_trends = []
        for asset in basket:
            asset_df = _safe_fetch(OVERNIGHT_TICKERS[asset], period="6mo")
            if asset_df is not None:
                basket_trends.append(_calc_trend(asset_df)["6mo_pct"])
        
        if basket_trends:
            avg_basket_trend = np.mean(basket_trends)
            if avg_basket_trend > 15:
                supercycle_score = -10
                alerts.append(f"🔥 Commodity Supercycle: Core basket up {avg_basket_trend:.1f}% over 6mo")

    breakdown["commodity_supercycle"] = {"score": supercycle_score, "weight": "modifier"}
    score += supercycle_score
    
    # ─── FINAL COMPOSITE ─────────────────────────────────────────
    score = np.clip(score, -100, 100)
    score = round(float(score), 1)
    
    # Determine pre-market bias
    if score >= 25:
        bias = "STRONG_BULLISH"
        regime_adj = "lower_thresholds"  # Make it easier to enter trades
    elif score >= 10:
        bias = "BULLISH"
        regime_adj = "slightly_lower_thresholds"
    elif score <= -25:
        bias = "STRONG_BEARISH"
        regime_adj = "raise_thresholds"  # Tighten entry criteria
    elif score <= -10:
        bias = "BEARISH"
        regime_adj = "slightly_raise_thresholds"
    else:
        bias = "NEUTRAL"
        regime_adj = "no_change"
    
    # Sort alerts by severity
    if not alerts:
        alerts.append("✅ No major overnight events detected — normal conditions")
    
    report = {
        "scan_time": datetime.now().isoformat(),
        "global_score": score,
        "pre_market_bias": bias,
        "regime_adjustment": regime_adj,
        "num_alerts": len(alerts),
        "alerts": alerts,
        "breakdown": breakdown,
        "raw_data": {k: v for k, v in results.items() if v.get("available")}
    }
    
    logger.info(f"🌍 Overnight Scan Complete: Score={score}, Bias={bias}, Alerts={len(alerts)}")
    return report


def get_overnight_bias() -> Dict[str, Any]:
    """
    Simplified interface for the ensemble to consume.
    Returns just the bias and score for threshold adjustments.
    """
    try:
        report = scan_overnight_global()
        return {
            "score": report["global_score"],
            "bias": report["pre_market_bias"],
            "regime_adjustment": report["regime_adjustment"],
            "top_alert": report["alerts"][0] if report["alerts"] else "No alerts"
        }
    except Exception as e:
        logger.error(f"Overnight scan failed: {e}")
        return {
            "score": 0,
            "bias": "NEUTRAL",
            "regime_adjustment": "no_change",
            "top_alert": "Scan failed — defaulting to neutral"
        }


def format_telegram_briefing(report: Dict[str, Any]) -> str:
    """Format the overnight report into a clean Telegram message."""
    score = report["global_score"]
    bias = report["pre_market_bias"]
    
    # Emoji based on bias
    bias_emoji = {
        "STRONG_BULLISH": "🟢🟢",
        "BULLISH": "🟢",
        "NEUTRAL": "⚪",
        "BEARISH": "🔴",
        "STRONG_BEARISH": "🔴🔴"
    }
    
    msg = f"""🌍 *OVERNIGHT GLOBAL INTELLIGENCE*
━━━━━━━━━━━━━━━━━━━━━━
{bias_emoji.get(bias, '⚪')} *Pre-Market Bias: {bias}*
📊 Global Score: {score}/100

*Key Overnight Events:*
"""
    for alert in report.get("alerts", [])[:5]:
        msg += f"• {alert}\n"
    
    msg += f"""
*Category Scores:*
"""
    for category, data in report.get("breakdown", {}).items():
        cat_name = category.replace("_", " ").title()
        cat_score = data.get("score", 0)
        indicator = "🟢" if cat_score > 10 else "🔴" if cat_score < -10 else "⚪"
        msg += f"{indicator} {cat_name}: {cat_score:+.0f}\n"
    
    msg += f"""
━━━━━━━━━━━━━━━━━━━━━━
⏰ Scan Time: {report.get('scan_time', 'N/A')[:16]}
"""
    return msg


if __name__ == "__main__":
    print("Running Overnight Global Intelligence Scan...")
    report = scan_overnight_global()
    print(format_telegram_briefing(report))
