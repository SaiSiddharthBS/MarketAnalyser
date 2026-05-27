import yfinance as yf
df = yf.download("AXISBANK.NS", period="5d", interval="1d")
print(df)
