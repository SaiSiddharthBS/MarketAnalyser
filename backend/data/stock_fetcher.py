"""
MarketPulse — Stock & Index Data Fetcher
Uses yfinance for NSE/BSE/Global market data.
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import ssl
import requests

# Fix Mac SSL issue
ssl._create_default_https_context = ssl._create_unverified_context

# Bypassing Cloud IP Blocks (Render/Heroku)
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
})


def get_stock_data(symbol, period="1y", interval="1d", exchange="NS"):
    """Fetch OHLCV data for a stock."""
    ticker = f"{symbol}.{exchange}" if exchange else symbol
    try:
        data = yf.download(ticker, period=period, interval=interval, progress=False, session=session)
        if data.empty:
            return None
        # Flatten multi-level columns if present
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        data.index = data.index.strftime("%Y-%m-%d") if interval == "1d" else data.index.strftime("%Y-%m-%d %H:%M")
        return data.reset_index().to_dict("records")
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None


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
        data = yf.download(index_symbol, period=period, interval="1d", progress=False, session=session)
        if data.empty:
            return None
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        data.index = data.index.strftime("%Y-%m-%d")
        return data.reset_index().to_dict("records")
    except Exception as e:
        print(f"Error fetching index {index_symbol}: {e}")
        return None


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

    for name, symbol in all_symbols.items():
        try:
            # Note: yf.Ticker().history() uses its own curl_cffi session internally
            # Do NOT pass requests.Session here — it causes errors in yfinance 0.2.40+
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2d")
            if hist.empty:
                continue
            current = hist["Close"].iloc[-1]
            prev = hist["Close"].iloc[-2] if len(hist) > 1 else current
            change = current - prev
            change_pct = (change / prev) * 100 if prev else 0
            result[name] = {
                "value": round(float(current), 2),
                "change": round(float(change), 2),
                "change_pct": round(float(change_pct), 2),
            }
        except Exception as e:
            print(f"Error fetching {name}: {e}")

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
        data = yf.download(tickers, period="1d", progress=False, session=session)
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
