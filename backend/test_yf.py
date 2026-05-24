import yfinance as yf
print("Downloading...")
df = yf.download("RELIANCE.NS", period="6mo", interval="1d")
print("Done!")
print(df.head())
