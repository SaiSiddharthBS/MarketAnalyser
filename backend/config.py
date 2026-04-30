"""
MarketPulse - Agent Alpha
Configuration Module
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Server
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# FRED
FRED_API_KEY = os.getenv("FRED_API_KEY", "")

# Database
DB_PATH = BASE_DIR / "data" / "marketpulse.db"

# Market Settings
MARKET_OPEN = "09:15"
MARKET_CLOSE = "15:30"
TIMEZONE = "Asia/Kolkata"

# Stock Universe
NIFTY_50_SYMBOLS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "HINDUNILVR", "ITC", "SBIN", "BHARTIARTL", "KOTAKBANK",
    "LT", "AXISBANK", "ASIANPAINT", "MARUTI", "TITAN",
    "SUNPHARMA", "BAJFINANCE", "WIPRO", "HCLTECH", "ULTRACEMCO",
    "NESTLEIND", "NTPC", "POWERGRID", "TATAMOTORS", "TATASTEEL",
    "M&M", "ONGC", "JSWSTEEL", "ADANIPORTS", "COALINDIA",
    "BAJAJFINSV", "TECHM", "GRASIM", "INDUSINDBK", "HINDALCO",
    "DRREDDY", "BPCL", "CIPLA", "EICHERMOT", "DIVISLAB",
    "HEROMOTOCO", "APOLLOHOSP", "BRITANNIA", "SBILIFE", "TATACONSUM",
    "BAJAJ-AUTO", "HDFCLIFE", "SHRIRAMFIN", "LTIM", "ADANIENT",
]

# User's MF Scheme Codes (from AMFI)
USER_MF_HOLDINGS = {
    "ICICI Prudential Nifty 50 Index Fund - Direct Plan": {
        "scheme_code": "120620",
        "invested": 40998,
        "units": 161.7885,
    },
    "SBI Gold Fund - Direct Plan - Growth": {
        "scheme_code": "119788",
        "invested": 35998,
        "units": 718.7280,
    },
    "ICICI Prudential Multi-Asset Fund - Direct Plan - Growth": {
        "scheme_code": "120334",
        "invested": 27999,
        "units": 31.1605,
    },
}

# Risk Profile
RISK_PROFILE = {
    "max_single_stock_pct": 5.0,      # Max 5% in any single stock
    "max_sector_pct": 25.0,           # Max 25% in any sector
    "max_drawdown_pct": 15.0,         # Circuit breaker at 15% drawdown
    "kelly_fraction": 0.3,            # Conservative 0.3x Kelly
    "risk_tolerance": "moderate",      # moderate for the user
}

# Technical Analysis Defaults
TA_PARAMS = {
    "rsi_period": 14,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "bb_period": 20,
    "bb_std": 2,
    "ema_short": 20,
    "ema_medium": 50,
    "ema_long": 200,
    "atr_period": 14,
}
