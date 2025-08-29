"""
Main entry point for the Universal Web Scraper.
"""

import argparse
import asyncio
import os
import sys
from datetime import timedelta
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from crawlee import ConcurrencySettings, Request
from crawlee.crawlers import PlaywrightCrawler
from crawlee.fingerprint_suite import DefaultFingerprintGenerator
from crawlee.playwright_crawler import PlaywrightCrawler
from dotenv import load_dotenv

from core.logger import logger
from core.parser_manager import ParserManager
from core.parser_registry import create_parser_registry
from core.proxy_config import create_proxy_configuration
from core.seeds import resolve_seeds
from routes import build_router
from src.core.logger import logger
from src.core.parser_manager import ParserManager
from src.core.parser_registry import create_parser_registry
from src.core.proxy_config import create_proxy_configuration
from src.core.seeds import resolve_seeds
from src.routes import create_router


async def main() -> None:
    """Main application entry point."""
    load_dotenv()

    parser = argparse.ArgumentParser(description="Universal Web Scraper")
    parser.add_argument("--url", help="Single URL to scrape")
    parser.add_argument(
        "--file",
        help="File containing URLs to scrape",
        default=os.getenv("SEEDS_FILE", "seeds.txt"),
    )
    parser.add_argument("--parser", help="Force specific parser ID")
    parser.add_argument("--label", help="CSS selector for link discovery")
    parser.add_argument("--max-requests", type=int, help="Maximum requests to process")
    parser.add_argument(
        "--simple", action="store_true", help="Simple mode - no link discovery"
    )

    args = parser.parse_args()

    # Initialize components
    registry = await create_parser_registry()
    manager = ParserManager(registry)
    router = build_router(registry=registry, manager=manager)
    seeds = await resolve_seeds(args)

    # Configure proxy
    proxy_config = await create_proxy_configuration()
    if proxy_config:
        logger.info("Proxy configuration enabled")

    # Configure fingerprint generator (Crawlee built-in)
    fingerprint_enabled = os.getenv("ENABLE_FINGERPRINTING", "true").lower()
    fingerprint_generator = None

    if fingerprint_enabled not in ("false", "0", "no", "off"):
        fingerprint_generator = DefaultFingerprintGenerator()
        logger.info("Fingerprint generation: ENABLED (Crawlee built-in)")
    else:
        logger.info("Fingerprint generation: DISABLED")

    # Configure crawler options
    concurrency_settings = ConcurrencySettings(
        max_concurrency=int(os.getenv("MAX_CONCURRENCY", "2"))
    )

    crawler_kwargs = {
        "request_handler": router,
        "concurrency_settings": concurrency_settings,
        "request_handler_timeout": timedelta(seconds=120),
        "browser_type": "chromium",
        "headless": True,
    }

    # Add fingerprint generator if enabled
    if fingerprint_generator:
        crawler_kwargs["fingerprint_generator"] = fingerprint_generator

    if proxy_config:
        crawler_kwargs["proxy_configuration"] = proxy_config

    # Create and run crawler
    crawler = PlaywrightCrawler(**crawler_kwargs)

    # Prepare requests
    requests = []
    for seed in seeds:
        user_data = {}
        if seed.get("parser"):
            user_data["parser"] = seed["parser"]

        request = Request.from_url(
            url=seed["url"],
            label=seed.get("label"),
            user_data=user_data if user_data else {},
        )
        requests.append(request)

    await crawler.run(requests)


if __name__ == "__main__":
    asyncio.run(main())
