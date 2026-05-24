import asyncio
from arena.paper_trading import get_latest_portfolio

print("Calling get_latest_portfolio...")
try:
    res = get_latest_portfolio()
    print("Result:", res)
except Exception as e:
    print("Error:", e)
