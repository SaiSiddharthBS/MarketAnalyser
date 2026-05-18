"""
Agent Alpha v4.0 - Arena Scheduler
Trigger point for GitHub Actions or local cron to run the arena execution.
"""
import logging
from arena.paper_trading import execute_daily_arena

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Triggering Arena execution...")
    try:
        execute_daily_arena()
    except Exception as e:
        logger.error(f"Arena execution failed: {e}", exc_info=True)
