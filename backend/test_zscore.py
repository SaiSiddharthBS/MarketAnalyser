import yfinance as yf
import pandas as pd
import numpy as np
df1 = yf.download("AXISBANK.NS", period="6mo", interval="1d")['Close'].dropna()
df2 = yf.download("SBIN.NS", period="6mo", interval="1d")['Close'].dropna()
data = pd.concat([df1, df2], axis=1, join='inner')
data.columns = ["A", "B"]
data['spread'] = np.log(data["A"]) - np.log(data["B"])
data['mean_spread'] = data['spread'].rolling(window=60).mean()
data['std_spread'] = data['spread'].rolling(window=60).std()
data['z_score'] = (data['spread'] - data['mean_spread']) / data['std_spread']
print("Latest Spread:", data['spread'].iloc[-1].item())
print("Latest Mean:", data['mean_spread'].iloc[-1].item())
print("Latest Std:", data['std_spread'].iloc[-1].item())
print("Latest Z-Score:", data['z_score'].iloc[-1].item())
