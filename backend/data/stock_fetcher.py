"""
MarketPulse — Stock & Index Data Fetcher
Uses yfinance for NSE/BSE/Global market data with direct Yahoo API fallback for cloud environments.
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import ssl
import requests
from .cache import cache

# Fix Mac SSL issue
ssl._create_default_https_context = ssl._create_unverified_context

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

# Period to Yahoo API range mapping
_PERIOD_MAP = {
    "1d": "1d", "5d": "5d", "1mo": "1mo", "3mo": "3mo",
    "6mo": "6mo", "1y": "1y", "2y": "2y", "3y": "5y", "5y": "5y", "max": "max",
}


def download_ohlcv(symbol, period="1y", interval="1d"):
    """
    Robust OHLCV downloader. Tries yf.download first, then falls back to
    the direct Yahoo Finance v8 chart API to bypass cloud IP blocks.
    Returns a pandas DataFrame or None.
    """
    # Use Direct Yahoo Finance API (bypasses cloud IP blocks and Crumb errors)
    try:
        yahoo_range = _PERIOD_MAP.get(period, "6mo")
        url = f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}?interval={interval}&range={yahoo_range}"
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return None
        data = r.json()
        result = data["chart"]["result"][0]
        timestamps = result["timestamp"]
        quotes = result["indicators"]["quote"][0]

        df = pd.DataFrame({
            "Open": quotes.get("open", []),
            "High": quotes.get("high", []),
            "Low": quotes.get("low", []),
            "Close": quotes.get("close", []),
            "Volume": quotes.get("volume", []),
        }, index=pd.to_datetime(timestamps, unit="s"))
        df.index.name = "Date"
        df = df.dropna(subset=["Close"])
        if not df.empty:
            return df
    except Exception as e:
        print(f"Yahoo API fallback failed for {symbol}: {e}")

    return None


def is_market_open():
    try:
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo("Asia/Kolkata"))
    except Exception:
        now = datetime.utcnow() + timedelta(hours=5, minutes=30)
    
    if now.weekday() >= 5:
        return False
        
    market_start = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_end = now.replace(hour=15, minute=30, second=0, microsecond=0)
    
    return market_start <= now <= market_end

def get_stock_data(symbol, period="1y", interval="1d", exchange="NS"):
    """Fetch OHLCV data for a stock with caching."""
    ticker = f"{symbol}.{exchange}" if exchange else symbol
    
    cache_key = f"ohlcv_{ticker}_{period}_{interval}"
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data
        
    try:
        df = download_ohlcv(ticker, period=period, interval=interval)
        
        from .data_validator import validator, DataQualityError
        validator.strict_mode = True
        df, report = validator.validate_ohlcv(df, ticker)
        
        if df is None or df.empty:
            raise DataQualityError(f"Data became empty after validation for {ticker}")
            
        df.index = df.index.strftime("%Y-%m-%d") if interval == "1d" else df.index.strftime("%Y-%m-%d %H:%M")
        result = df.reset_index().to_dict("records")
        
        # TTL: 15 mins during market hours, 12 hours otherwise
        ttl = 15 * 60 if is_market_open() else 12 * 60 * 60
        cache.set(cache_key, result, ttl=ttl)
        
        return result
    except DataQualityError:
        raise
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None


def _get_delivery_percentage(symbol: str) -> float:
    """Fetch delivery percentage from NSE. Returns 100.0 if failed to bypass filters."""
    cache_key = f"delivery_pct_{symbol}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        from data.fii_dii_fetcher import _get_nse_session
        session = _get_nse_session()
        from urllib.parse import quote
        safe_symbol = quote(symbol)
        
        url = f"https://www.nseindia.com/api/quote-equity?symbol={safe_symbol}"
        r = session.get(url, timeout=10)
        
        if r.status_code == 200:
            data = r.json()
            dp = data.get("securityWiseDP", {})
            pct = dp.get("deliveryToTradedQuantity", 100.0)
            
            if pct is None:
                pct = 100.0
            pct = float(pct)
            
            cache.set(cache_key, pct, ttl=3600 * 4) # cache for 4 hours
            return pct
    except Exception as e:
        pass
        
    # Cache the fallback so we don't hammer the blocked API
    cache.set(cache_key, 100.0, ttl=3600 * 4)
    return 100.0


def get_stock_info(symbol, exchange="NS"):
    """Get fundamental info for a stock."""
    ticker = f"{symbol}.{exchange}" if exchange else symbol
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "symbol": symbol,
            "name": info.get("longName", symbol),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": info.get("trailingPE", None),
            "pb_ratio": info.get("priceToBook", None),
            "roe": info.get("returnOnEquity", None),
            "debt_to_equity": info.get("debtToEquity", None),
            "dividend_yield": info.get("dividendYield", None),
            "eps": info.get("trailingEps", None),
            "book_value": info.get("bookValue", None),
            "current_price": info.get("currentPrice", info.get("regularMarketPrice", None)),
            "day_high": info.get("dayHigh", None),
            "day_low": info.get("dayLow", None),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh", None),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow", None),
            "avg_volume": info.get("averageVolume", None),
        }
    except Exception as e:
        print(f"Error fetching info for {ticker}: {e}")
        return None


def get_index_data(index_symbol, period="6mo"):
    """Fetch index data. Common indices: ^NSEI (Nifty50), ^BSESN (Sensex)."""
    try:
        df = download_ohlcv(index_symbol, period=period, interval="1d")
        if df is None or df.empty:
            return None
        df.index = df.index.strftime("%Y-%m-%d")
        return df.reset_index().to_dict("records")
    except Exception as e:
        print(f"Error fetching index {index_symbol}: {e}")
        return None


import pytz
from datetime import time

def get_market_status():
    """Determine the current market status based on IST time."""
    tz = pytz.timezone("Asia/Kolkata")
    now = datetime.now(tz)
    
    if now.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
        return "WEEKEND"
    
    current_time = now.time()
    market_open = time(9, 15)
    market_close = time(15, 30)
    
    if current_time < market_open:
        return "PRE_MARKET"
    elif current_time <= market_close:
        return "OPEN"
    else:
        return "CLOSED"

def get_market_overview():
    """Get current snapshot of major indices and indicators."""
    indices = {
        "NIFTY_50": "^NSEI",
        "SENSEX": "^BSESN",
        "NIFTY_BANK": "^NSEBANK",
        "S&P_500": "^GSPC",
        "NASDAQ": "^IXIC",
        "INDIA_VIX": "^INDIAVIX",
    }
    commodities = {
        "GOLD_USD": "GC=F",
        "CRUDE_OIL": "CL=F",
        "USD_INR": "USDINR=X",
    }

    result = {}
    all_symbols = {**indices, **commodities}
    
    status = get_market_status()
    tz = pytz.timezone("Asia/Kolkata")
    timestamp_str = datetime.now(tz).isoformat()

    for name, symbol in all_symbols.items():
        current, prev = None, None
        try:
            # Attempt 1: Standard yfinance
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2d")
            if not hist.empty:
                current = float(hist["Close"].iloc[-1])
                prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else current
        except Exception:
            pass
            
        if current is None:
            # Attempt 2: Direct Yahoo Finance API Fallback (Bypasses yfinance block)
            try:
                import requests
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                url = f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=2d"
                res = requests.get(url, headers=headers, timeout=5)
                data = res.json()
                quotes = data['chart']['result'][0]['indicators']['quote'][0]['close']
                quotes = [q for q in quotes if q is not None]
                if len(quotes) >= 1:
                    current = float(quotes[-1])
                    prev = float(quotes[-2]) if len(quotes) > 1 else current
            except Exception as fallback_e:
                print(f"Fallback failed for {name}: {fallback_e}")

        if current is not None and prev is not None:
            change = current - prev
            change_pct = (change / prev) * 100 if prev else 0
            result[name] = {
                "value": round(current, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
            }

    return result


def get_ltp(symbol, exchange="NS"):
    """Get last traded price for a stock."""
    ticker = f"{symbol}.{exchange}" if exchange else symbol
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d")
        if hist.empty:
            return None
        return round(float(hist["Close"].iloc[-1]), 2)
    except Exception:
        return None


def get_bulk_ltp(symbols, exchange="NS"):
    """Get LTP for multiple stocks at once."""
    tickers = [f"{s}.{exchange}" for s in symbols]
    try:
        data = yf.download(tickers, period="1d", progress=False)
        if data.empty:
            return {}
        result = {}
        if isinstance(data.columns, pd.MultiIndex):
            for i, sym in enumerate(symbols):
                ticker = f"{sym}.{exchange}"
                try:
                    result[sym] = round(float(data["Close"][ticker].iloc[-1]), 2)
                except (KeyError, IndexError):
                    pass
        return result
    except Exception as e:
        print(f"Error in bulk LTP: {e}")
        return {}
