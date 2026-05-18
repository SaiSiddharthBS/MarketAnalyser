"""
Task 15: Structured Logging Framework.
Configures Python logging with structured JSON-like output and
provides a request-timing middleware for FastAPI.
"""
import logging
import sys
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


def setup_logging(level: str = "INFO"):
    """Configure the root marketpulse logger with structured output."""
    log_format = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))

    root_logger = logging.getLogger("marketpulse")
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Quiet noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("yfinance").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)

    return root_logger


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Log every API call with method, path, status, and response time."""

    async def dispatch(self, request: Request, call_next):
        logger = logging.getLogger("marketpulse.http")
        start = time.perf_counter()

        response = await call_next(request)

        elapsed_ms = (time.perf_counter() - start) * 1000
        # Skip static file requests and health checks to reduce noise
        path = request.url.path
        if not path.startswith("/static") and path != "/favicon.ico":
            logger.info(
                "%s %s → %d (%.0fms)",
                request.method, path, response.status_code, elapsed_ms
            )

        return response
