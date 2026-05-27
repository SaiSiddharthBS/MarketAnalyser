import asyncio
from database import Database
async def main():
    db = Database()
    await db.connect()
    res = await db.fetch_all("SELECT * FROM paper_portfolio ORDER BY date DESC LIMIT 1")
    print(res)
    await db.close()
asyncio.run(main())
