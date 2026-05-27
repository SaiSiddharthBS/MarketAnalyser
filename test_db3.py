import asyncio
from backend.database.db import Database
from dotenv import load_dotenv
load_dotenv()
async def main():
    db = Database()
    await db.connect()
    res = await db.fetch_all("SELECT id, date, total_equity, created_at FROM paper_portfolio ORDER BY created_at DESC LIMIT 5")
    for r in res: print(dict(r))
    await db.close()
asyncio.run(main())
