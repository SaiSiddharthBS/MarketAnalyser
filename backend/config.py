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

# ─── Stock Universe ─────────────────────────────────────────────

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

# ─── Sector Indices ─────────────────────────────────────────────
# Each sector has: name, yahoo_index (for sector strength calc), symbols

SECTOR_INDICES = {
    "NIFTY_50": {
        "name": "Nifty 50",
        "yahoo_index": "^NSEI",
        "symbols": NIFTY_50_SYMBOLS,
    },
    "NIFTY_BANK": {
        "name": "Nifty Bank",
        "yahoo_index": "^NSEBANK",
        "symbols": [
            "HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK",
            "INDUSINDBK", "BAJFINANCE", "BAJAJFINSV", "BANDHANBNK",
            "IDFCFIRSTB", "PNB", "FEDERALBNK",
        ],
    },
    "NIFTY_IT": {
        "name": "Nifty IT",
        "yahoo_index": "^CNXIT",
        "symbols": [
            "TCS", "INFY", "WIPRO", "HCLTECH", "TECHM",
            "LTIM", "PERSISTENT", "COFORGE", "MPHASIS", "LTTS",
        ],
    },
    "NIFTY_PHARMA": {
        "name": "Nifty Pharma",
        "yahoo_index": "^CNXPHARMA",
        "symbols": [
            "SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB", "APOLLOHOSP",
            "BIOCON", "AUROPHARMA", "TORNTPHARM", "LUPIN", "ALKEM",
        ],
    },
    "NIFTY_AUTO": {
        "name": "Nifty Auto",
        "yahoo_index": "^CNXAUTO",
        "symbols": [
            "MARUTI", "TATAMOTORS", "M&M", "BAJAJ-AUTO", "HEROMOTOCO",
            "EICHERMOT", "ASHOKLEY", "BOSCHLTD", "BALKRISIND", "BHARATFORG",
            "MOTHERSON", "TVSMOTOR", "MRF", "EXIDEIND", "TIINDIA",
        ],
    },
    "NIFTY_METAL": {
        "name": "Nifty Metal",
        "yahoo_index": "^CNXMETAL",
        "symbols": [
            "TATASTEEL", "JSWSTEEL", "HINDALCO", "COALINDIA", "VEDL",
            "NMDC", "SAIL", "NATIONALUM", "APLAPOLLO", "JINDALSTEL",
            "RATNAMANI", "MOIL", "WELCORP",
        ],
    },
    "NIFTY_FMCG": {
        "name": "Nifty FMCG",
        "yahoo_index": "^CNXFMCG",
        "symbols": [
            "HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "TATACONSUM",
            "DABUR", "MARICO", "GODREJCP", "COLPAL", "VBL",
            "EMAMILTD", "RADICO", "PGHH", "UNITDSPR",
        ],
    },
    "NIFTY_ENERGY": {
        "name": "Nifty Energy",
        "yahoo_index": "^CNXENERGY",
        "symbols": [
            "RELIANCE", "NTPC", "POWERGRID", "ONGC", "BPCL",
            "COALINDIA", "IOC", "GAIL", "ADANIGREEN", "TATAPOWER",
            "NHPC", "SJVN", "IREDA",
        ],
    },
    "NIFTY_INFRA": {
        "name": "Nifty Infrastructure",
        "yahoo_index": "^CNXINFRA",
        "symbols": [
            "LT", "ADANIPORTS", "ULTRACEMCO", "GRASIM", "BHARTIARTL",
            "POWERGRID", "NTPC", "SIEMENS", "ABB", "HAVELLS",
            "CUMMINSIND", "BEL", "HAL",
        ],
    },
    "NIFTY_PSU_BANK": {
        "name": "Nifty PSU Bank",
        "yahoo_index": "^CNXPSUBANK",
        "symbols": [
            "SBIN", "PNB", "BANKBARODA", "CANBK", "UNIONBANK",
            "IOB", "INDIANB", "CENTRALBK", "BANKINDIA", "MAHABANK",
            "UCOBANK", "PSB",
        ],
    },
    "NIFTY_REALTY": {
        "name": "Nifty Realty",
        "yahoo_index": "^CNXREALTY",
        "symbols": [
            "DLF", "GODREJPROP", "OBEROIRLTY", "PRESTIGE", "PHOENIXLTD",
            "BRIGADE", "SOBHA", "SUNTECK", "LODHA", "MAHLIFE",
        ],
    },
    # ─── Tradable Instruments (same screener logic) ───────────
    "ETFS": {
        "name": "ETFs (Exchange Traded)",
        "yahoo_index": "^NSEI",
        "symbols": [
            "NIFTYBEES", "BANKBEES", "JUNIORBEES", "SETFNIF50",
            "ITBEES", "PSUBNKBEES", "CPSEETF", "MOM50",
            "MON100", "MIDCPBEES",
        ],
    },
    "GOLD_ETFS": {
        "name": "Gold & Commodity ETFs",
        "yahoo_index": "GC=F",
        "symbols": [
            "GOLDBEES", "GOLDSHARE", "LIQUIDBEES", "SILVERBEES",
        ],
    },
    "REITS_INVITS": {
        "name": "REITs & InvITs",
        "yahoo_index": "^NSEI",
        "symbols": [
            "MINDSPACE", "BROOKFIELD", "EMBASSY", "IRBINVIT",
            "INDIGRID", "POWERGRID-INVIT",
        ],
    },
}

# All segment keys for easy iteration
ALL_SEGMENTS = list(SECTOR_INDICES.keys())

# ─── User's MF Holdings ────────────────────────────────────────

USER_MF_HOLDINGS = {
    "ICICI Prudential Nifty 50 Index Fund": {
        "scheme_code": "120620",
        "invested": 40998,
        "units": 161.7885,
    },
    "SBI Gold Fund": {
        "scheme_code": "119788",
        "invested": 35998,
        "units": 718.7280,
    },
    "ICICI Prudential Multi Asset Fund": {
        "scheme_code": "120334",
        "invested": 27999,
        "units": 31.1605,
    },
}

# ─── Risk Profile ──────────────────────────────────────────────

RISK_PROFILE = {
    "max_single_stock_pct": 5.0,      # Max 5% in any single stock
    "max_sector_pct": 25.0,           # Max 25% in any sector
    "max_drawdown_pct": 15.0,         # Circuit breaker at 15% drawdown
    "kelly_fraction": 0.3,            # Conservative 0.3x Kelly
    "risk_tolerance": "moderate",      # moderate for the user
}

# ─── Technical Analysis Defaults ───────────────────────────────

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

# ─── 5-Point Signal Thresholds ─────────────────────────────────

SIGNAL_THRESHOLDS = {
    "STRONG_BUY": 80,   # 🚀 All factors aligned
    "BUY": 60,          # 🟢 Good setup
    "WATCH": 45,        # 🟡 Forming but not triggered
    "WEAKENING": 25,    # 🟠 Momentum fading
    "EXIT": 0,          # 🔴 Trend broken
}

SIGNAL_LABELS = {
    "STRONG_BUY": "🚀 Strong Buy",
    "BUY": "🟢 Buy",
    "WATCH": "🟡 Watch",
    "WEAKENING": "🟠 Weakening",
    "EXIT": "🔴 Exit",
}
