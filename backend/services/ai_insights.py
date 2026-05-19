import os
import google.generativeai as genai
import logging
import json

logger = logging.getLogger(__name__)

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

def get_gemini_model():
    return genai.GenerativeModel("gemini-2.5-flash")

async def get_stock_briefing(symbol: str, fundamentals: dict, headlines: list) -> dict:
    """Generate an AI investment briefing using Gemini Flash."""
    if not api_key:
        return {"error": "GEMINI_API_KEY not configured"}
        
    model = get_gemini_model()
    prompt = f"""You are an elite quantitative equity research analyst for a high-frequency trading firm.
    Produce a concise briefing for {symbol}.
    
    Fundamentals: {json.dumps(fundamentals)}
    Recent headlines: {json.dumps(headlines)}
    
    Provide your output in exactly this JSON format:
    {{
        "bull_case": "2-3 sentences explaining the bull thesis",
        "bear_case": "2-3 sentences explaining the bear thesis",
        "key_risks": "1-2 sentences highlighting immediate risks"
    }}
    
    Only output valid JSON.
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        return json.loads(text.strip())
    except Exception as e:
        logger.error(f"Failed to generate stock briefing: {e}")
        return {"error": str(e)}

async def explain_arena_decision(regime: str, trades: list, standings: dict = None) -> str:
    """Explain why Arena chose to trade or stand aside."""
    if not api_key:
        return "AI analysis unavailable (missing GEMINI_API_KEY)."
        
    model = get_gemini_model()
    prompt = f"""You are 'Agent Alpha', an autonomous quantitative trading engine.
    Explain your daily trading decisions to your human portfolio manager in a concise, authoritative tone (max 3 sentences).
    
    Market regime: {regime}
    Trades executed today: {json.dumps(trades)}
    
    If no trades were executed, explain why based on the regime. If trades were executed, briefly justify them.
    Do not use introductory filler like "Here is the explanation". Just give the direct insight.
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Failed to generate arena explanation: {e}")
        return f"System executed normally under {regime} regime."
        
async def generate_risk_insights(portfolio_stats: dict) -> str:
    """Generate portfolio risk narrative."""
    if not api_key:
        return "AI analysis unavailable."
        
    model = get_gemini_model()
    prompt = f"""You are the Chief Risk Officer for Agent Alpha.
    Analyze these portfolio statistics and provide a 2-3 sentence risk narrative for the portfolio manager.
    
    Stats: {json.dumps(portfolio_stats)}
    
    Highlight max drawdown, win rate, and overall risk posture. Be concise and professional.
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Failed to generate risk insight: {e}")
        return "Risk analysis temporarily unavailable."
