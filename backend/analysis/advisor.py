"""
MarketPulse — AI Advisor Module
Acts as a Personal Financial Planner using Gemini.
"""
import os
import traceback
from datetime import datetime
try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

def generate_financial_advice(portfolio_data, market_data, news_data):
    """Generate personalized financial advice using Gemini."""
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not HAS_GENAI or not api_key:
        return "⚠️ Gemini API Key not found or `google-genai` not installed. Please add GEMINI_API_KEY to your Render environment variables to activate your Personal AI Advisor."

    try:
        client = genai.Client(api_key=api_key)
        
        # Construct the context prompt
        prompt = f"""
You are Agent Alpha, a world-class, proactive Personal Financial Advisor and Wealth Manager. 
Your client (Sai) relies on you to monitor their portfolio, analyze market conditions, and give explicit, actionable advice.

CURRENT DATE: {datetime.now().strftime('%A, %B %d, %Y')}

1. MARKET CONTEXT:
{market_data}

2. LATEST NEWS SENTIMENT:
{news_data}

3. CLIENT'S PORTFOLIO:
{portfolio_data}

YOUR MISSION:
Write a concise, highly personalized briefing for Sai.
- You are completely agnostic to asset classes. You analyze EVERYTHING: Stocks, MFs, Gold, FDs, Bonds, Crypto, PPF, NPS, Real Estate REITs, and Forex.
- Do NOT just list prices. Synthesize what the macro-economic environment means for their specific holdings.
- Be highly proactive. If you see an unrepresented asset class that is currently at a historic buying opportunity (e.g., "Crypto is crashing, consider allocating 2% risk capital" or "Interest rates are peaking, lock in long-term FDs now"), you MUST tell them.
- If a specific stock/sector drops significantly but fundamentals are strong, flag it as a buying opportunity. 
- Act like a top-tier fiduciary taking care of their holistic wealth.
- Keep the tone professional, sharp, and encouraging. Use bullet points for readability.
- Limit to 3-4 paragraphs max.

Format your response in clean Markdown.
"""

        response = client.models.generate_content(
            model='gemini-2.5-pro',
            contents=prompt,
        )
        return response.text

    except Exception as e:
        print(f"Error generating AI advice: {e}")
        return f"⚠️ I encountered an error generating your personalized advice today: {str(e)}"
