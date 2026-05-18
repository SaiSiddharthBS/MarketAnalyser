import sys
sys.path.insert(0, 'backend')
from data.stock_fetcher import get_stock_data
import pandas as pd
data = get_stock_data("RELIANCE", period="6mo", interval="1d")
df = pd.DataFrame(data)
print(df.columns)
print(df.head(2))
