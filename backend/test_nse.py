import time
from data.options_fetcher import fetch_options_chain
start = time.time()
fetch_options_chain("NIFTY")
print(f"Took {time.time() - start:.2f} seconds")
