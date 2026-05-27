import yfinance as yf
print("AXIS:", yf.download("AXISBANK.NS", period="1d", interval="1m")["Close"].iloc[-1].item())
print("SBIN:", yf.download("SBIN.NS", period="1d", interval="1m")["Close"].iloc[-1].item())
