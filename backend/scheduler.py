"""
MarketPulse - Agent Alpha
Main Entrypoint and Scheduler
"""
import schedule
import time
import logging
from datetime import datetime
import subprocess
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def run_overnight_intel():
    """Runs the Overnight Intel scanner."""
    logger.info("Executing Overnight Intel...")
    try:
        from analysis.overnight_intel import scan_overnight_global
        scan_overnight_global()
        logger.info("Overnight Intel executed successfully.")
    except Exception as e:
        logger.error(f"Error during Overnight Intel: {e}")

def run_daily_arena():
    """Runs the Daily Arena paper trading engine."""
    logger.info("Executing Daily Arena...")
    try:
        from database import backup_database
        backup_database()
        
        # We can call it directly, but arena/paper_trading.py has a __main__ block.
        # It's cleaner to import execute_daily_arena if we can.
        from arena.paper_trading import execute_daily_arena
        execute_daily_arena()
        logger.info("Daily Arena executed successfully.")
    except Exception as e:
        logger.error(f"Error during Daily Arena: {e}")

def main():
    from config import ROLE
    if ROLE != "master_executor":
        logger.warning(f"Scheduler skipped. ROLE is '{ROLE}'. Only 'master_executor' runs cron jobs.")
        # We can just idle loop to keep process alive if needed, or exit if docker doesn't care.
        # But wait, FastAPI runs this in a thread! So we can just return.
        return

    logger.info("Agent Alpha Main Scheduler Started as Master Node.")
    
    # 1. Overnight Intel runs at 08:30 AM IST (assuming system time is configured to IST via Docker)
    schedule.every().day.at("08:30").do(run_overnight_intel)
    
    # 2. Live Arena polling every 15 minutes during market hours
    # We will poll every 15 minutes. The execution engine itself handles state.
    def live_arena_wrapper():
        from data.stock_fetcher import is_market_open
        # DEMO MODE: Removing is_market_open() check so it runs 24/7 for testing
        run_daily_arena()

    def live_sentinel():
        try:
            from arena.paper_trading import track_live_positions
            track_live_positions()
        except Exception as e:
            logger.error(f"Live Sentinel Error: {e}")

    schedule.every(15).minutes.do(live_arena_wrapper)
    schedule.every(1).minute.do(live_sentinel)
    
    logger.info("Scheduled Tasks:")
    for job in schedule.get_jobs():
        logger.info(f" - {job}")
        
    # Kick off an immediate run on boot
    logger.info("Boot-up: Kicking off initial Arena run...")
    live_arena_wrapper()
        
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
