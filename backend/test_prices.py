import yfinance as yf
print("AXIS:", yf.download("AXISBANK.NS", period="5d")["Close"].iloc[-1].item())
print("SBIN:", yf.download("SBIN.NS", period="5d")["Close"].iloc[-1].item())
