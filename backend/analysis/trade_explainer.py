"""
MarketPulse — Trade Explainer
Generates plain-English "Why This Trade?" explanations using Gemini AI.
AI converts calculated indicator values into human-readable reasoning.
AI does NOT calculate the numbers — that's the indicator engine's job.
"""
import os
import time
import traceback
from google import genai


def explain_trade(stock_data):
    """Generate a 'Why This Trade?' explanation for a stock.

    Args:
        stock_data: Dictionary from get_technical_analysis() containing
                    score, signal, indicators, score_breakdown, market_regime, etc.

    Returns:
        String with bullet-point explanation, or None on failure.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    symbol = stock_data.get("symbol", "Unknown")
    score = stock_data.get("score", 0)
    signal = stock_data.get("signal", "WATCH")
    price = stock_data.get("price", 0)
    entry = stock_data.get("entry", 0)
    target = stock_data.get("target", 0)
    sl = stock_data.get("stop_loss", 0)
    rr = stock_data.get("risk_reward", 0)
    rvol = stock_data.get("rvol", 1.0)
    holding = stock_data.get("holding_period", "N/A")
    breakdown = stock_data.get("score_breakdown", {})
    indicators = stock_data.get("indicators", {})
    regime = stock_data.get("market_regime", {})
    signals_list = stock_data.get("signals", [])

    # Build context string from calculated data
    signals_text = "\n".join([
        f"  - {s['indicator']}: {s['signal']} (weight: {s['weight']})"
        for s in signals_list
    ])

    prompt = f"""You are Agent Alpha, a financial analysis assistant. 
Given the following CALCULATED technical data for {symbol} on NSE, write a clear "Why This Trade?" explanation.

STOCK: {symbol} | Price: ₹{price} | Score: {score}/100 | Signal: {signal}
Entry: ₹{entry} | Target: ₹{target} | Stop Loss: ₹{sl} | R/R: {rr}:1
RVOL: {rvol}x | Est. Holding: {holding}

SCORE BREAKDOWN:
  Trend: {breakdown.get('trend', 0)}/25
  Volume: {breakdown.get('volume', 0)}/20
  RSI/Momentum: {breakdown.get('rsi', 0)}/15
  Sector Strength: {breakdown.get('sector', 0)}/15
  Market Regime: {breakdown.get('regime', 0)}/15
  Risk-Reward: {breakdown.get('risk_reward', 0)}/10

INDICATORS:
  RSI: {indicators.get('rsi', 'N/A')}
  MACD Histogram: {indicators.get('macd_histogram', 'N/A')}
  EMA 20: {indicators.get('ema_20', 'N/A')} | EMA 50: {indicators.get('ema_50', 'N/A')} | EMA 200: {indicators.get('ema_200', 'N/A')}
  ADX: {indicators.get('adx', 'N/A')}
  ATR: {indicators.get('atr', 'N/A')}

SIGNALS DETECTED:
{signals_text}

MARKET REGIME:
  VIX: {regime.get('vix', 'N/A')} | Nifty Trend: {regime.get('nifty_trend', 'N/A')} | Regime Score: {regime.get('regime_score', 'N/A')}/15

RULES:
1. Write 5-8 bullet points explaining WHY this stock got this signal.
2. Use ✅ for bullish factors and ⚠️ for caution factors.
3. Mention specific numbers (RSI value, EMA levels, RVOL, R/R ratio).
4. End with: "Conviction Score: {score}/100 — {signal.replace('_', ' ')}"
5. Keep it under 150 words. Be direct. No fluff.
6. Do NOT recalculate any values — use the numbers provided above.
"""

    client = genai.Client(api_key=api_key)
    models = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-2.0-flash-lite']

    for model_name in models:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name, contents=prompt
                )
                return response.text
            except Exception as e:
                err = str(e)
                if '503' in err or 'unavailable' in err.lower():
                    time.sleep(5)
                else:
                    break

    return None
