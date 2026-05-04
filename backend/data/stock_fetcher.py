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
