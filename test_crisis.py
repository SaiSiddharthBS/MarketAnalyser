import asyncio
from backend.arena.paper_trading import execute_daily_arena

def mock_regime():
    return {"regime": "crisis", "vix_level": 35}

import backend.arena.paper_trading as pt
pt.get_current_market_regime = mock_regime

execute_daily_arena()
print("Success")
