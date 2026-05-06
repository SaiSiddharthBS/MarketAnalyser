"""
MarketPulse — Sector Rotation Engine
Evaluates all sectors and classifies each by relative strength vs Nifty 50.

Classifications:
  🔥 Strong      — outperforming Nifty, breadth expanding
  ↗  Improving   — momentum building, breadth turning positive
  →  Neutral     — in line with Nifty, no clear edge
  ↘  Weakening   — underperforming, breadth deteriorating
  ❄  Avoid       — trending down, negative breadth
"""
import ta
from data.stock_fetcher import download_ohlcv
from config import SECTOR_INDICES


def get_sector_rotation():
    """Analyse all sectors and return rotation heatmap data."""
    # Fetch Nifty 50 benchmark data
    nifty_df = download_ohlcv("^NSEI", period="3mo", interval="1d")
    if nifty_df is None or nifty_df.empty or len(nifty_df) < 20:
        return {"error": "Could not fetch Nifty 50 data", "sectors": []}

    nifty_5d = _pct_return(nifty_df, 5)
    nifty_10d = _pct_return(nifty_df, 10)
    nifty_20d = _pct_return(nifty_df, 20)

    results = []

    # Only evaluate actual sector indices (skip ETFs, REITs etc)
    sector_keys = [
        "NIFTY_50", "NIFTY_BANK", "NIFTY_IT", "NIFTY_PHARMA", "NIFTY_AUTO",
        "NIFTY_METAL", "NIFTY_FMCG", "NIFTY_ENERGY", "NIFTY_INFRA",
        "NIFTY_PSU_BANK", "NIFTY_REALTY",
    ]

    for key in sector_keys:
        seg = SECTOR_INDICES.get(key)
        if not seg:
            continue

        try:
            yahoo_idx = seg.get("yahoo_index", "^NSEI")
            sector_df = download_ohlcv(yahoo_idx, period="3mo", interval="1d")

            if sector_df is None or sector_df.empty or len(sector_df) < 20:
                results.append(_fallback_sector(key, seg["name"]))
                continue

            # Sector returns
            s_5d = _pct_return(sector_df, 5)
            s_10d = _pct_return(sector_df, 10)
            s_20d = _pct_return(sector_df, 20)

            # Relative strength vs Nifty (weighted average)
            rel_5d = s_5d - nifty_5d
            rel_10d = s_10d - nifty_10d
            rel_20d = s_20d - nifty_20d
            relative_strength = (rel_5d * 0.5) + (rel_10d * 0.3) + (rel_20d * 0.2)

            # Breadth: % of sector stocks above their 50 EMA
            breadth = _calc_breadth(seg["symbols"])

            # RVOL for sector index
            rvol = _calc_rvol(sector_df)

            # Composite score for classification
            composite = (relative_strength * 3) + (breadth - 50) * 0.1 + (rvol - 1) * 5

            # Classify
            if composite > 5:
                classification = "🔥 Strong"
                color = "#00e676"
            elif composite > 1.5:
                classification = "↗ Improving"
                color = "#69f0ae"
            elif composite > -1.5:
                classification = "→ Neutral"
                color = "#ffd740"
            elif composite > -5:
                classification = "↘ Weakening"
                color = "#ff9800"
            else:
                classification = "❄ Avoid"
                color = "#ff5252"

            results.append({
                "key": key,
                "name": seg["name"],
                "stock_count": len(seg["symbols"]),
                "classification": classification,
                "color": color,
                "relative_strength": round(relative_strength, 2),
                "returns": {
                    "5d": round(s_5d, 2),
                    "10d": round(s_10d, 2),
                    "20d": round(s_20d, 2),
                },
                "nifty_returns": {
                    "5d": round(nifty_5d, 2),
                    "10d": round(nifty_10d, 2),
                    "20d": round(nifty_20d, 2),
                },
                "breadth": round(breadth, 1),
                "rvol": round(rvol, 2),
                "composite_score": round(composite, 2),
            })

        except Exception as e:
            print(f"⚠️ Sector rotation error for {key}: {e}")
            results.append(_fallback_sector(key, seg["name"]))

    # Sort by composite score (strongest first)
    results.sort(key=lambda x: x.get("composite_score", 0), reverse=True)
    return {"sectors": results}


def _pct_return(df, days):
    """Calculate % return over N days."""
    if len(df) < days:
        return 0.0
    return (float(df["Close"].iloc[-1]) / float(df["Close"].iloc[-days]) - 1) * 100


def _calc_breadth(symbols, exchange="NS"):
    """Calculate % of stocks above their 50 EMA."""
    above = 0
    total = 0
    for sym in symbols[:15]:  # Limit to 15 to keep it fast
        try:
            ticker = f"{sym}.{exchange}"
            df = download_ohlcv(ticker, period="3mo", interval="1d")
            if df is not None and not df.empty and len(df) >= 50:
                ema50 = ta.trend.EMAIndicator(close=df["Close"], window=50).ema_indicator()
                if float(df["Close"].iloc[-1]) > float(ema50.iloc[-1]):
                    above += 1
                total += 1
        except Exception:
            pass
    return (above / total * 100) if total > 0 else 50.0


def _calc_rvol(df):
    """Calculate relative volume (current vs 20-day avg)."""
    if df is None or df.empty or len(df) < 20:
        return 1.0
    current_vol = float(df["Volume"].iloc[-1])
    avg_vol = float(df["Volume"].tail(20).mean())
    return round(current_vol / avg_vol, 2) if avg_vol > 0 else 1.0


def _fallback_sector(key, name):
    """Return a neutral fallback when data is unavailable."""
    return {
        "key": key,
        "name": name,
        "stock_count": 0,
        "classification": "→ Neutral",
        "color": "#ffd740",
        "relative_strength": 0,
        "returns": {"5d": 0, "10d": 0, "20d": 0},
        "nifty_returns": {"5d": 0, "10d": 0, "20d": 0},
        "breadth": 50,
        "rvol": 1.0,
        "composite_score": 0,
    }
