"""
Logging configuration using Loguru.
"""

import os
import sys

from loguru import logger

# Remove default handler
logger.remove()

# Configure structured logging format
log_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

# Add console handler
logger.add(
    sys.stderr,
    format=log_format,
    level=os.getenv("LOG_LEVEL", "INFO"),
    colorize=True,
)

# Add file handler for errors
logger.add(
    "scraper.log",
    format=log_format,
    level="ERROR",
    rotation="10 MB",
    retention="1 week",
    compression="zip",
)
