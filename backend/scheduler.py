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
    logger.info("Agent Alpha Main Scheduler Started.")
    
    # 1. Overnight Intel runs at 08:30 AM IST (assuming system time is configured to IST via Docker)
    schedule.every().day.at("08:30").do(run_overnight_intel)
    
    # 2. Daily Arena runs at 15:00 (3:00 PM IST)
    schedule.every().day.at("15:00").do(run_daily_arena)
    
    logger.info("Scheduled Tasks:")
    for job in schedule.get_jobs():
        logger.info(f" - {job}")
        
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
