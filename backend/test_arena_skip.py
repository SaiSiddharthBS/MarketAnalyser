import asyncio
from backend.arena.paper_trading import get_current_market_regime, get_technical_analysis, NIFTY_50_SYMBOLS, download_ohlcv
from backend.analysis.veto_engine import veto_engine

regime_data = get_current_market_regime()
regime = regime_data.get("regime", "unknown")
vix = regime_data.get("vix_level", 15)
print(f"Regime: {regime}, VIX: {vix}")

for symbol in NIFTY_50_SYMBOLS[:10]:
    print(f"\nEvaluating {symbol}...")
    df = download_ohlcv(f"{symbol}.NS", period="6mo", interval="1d")
    if df is None or len(df) < 50:
        print("  Skipped: Insufficient data")
        continue
    tech = get_technical_analysis(symbol)
    if not tech:
        print("  Skipped: Tech analysis failed")
        continue
    conf = tech.get("score", 0)
    sig = tech.get("signal", "NEUTRAL")
    veto = veto_engine.check_all_vetoes(symbol, {}, {"regime_state": regime, "vix": vix}, {})
    
    print(f"  Signal: {sig}, Score: {conf}")
    if veto.get("vetoed"):
        print(f"  Vetoed: {veto.get('reason')}")
