"""
Proxy configuration for free and paid proxies.
"""

import os
import random
from typing import Any, Dict, List, Optional

import httpx

from .logger import logger

# Free proxy lists (use with caution - these are public and may be unreliable)
FREE_PROXIES = [
    "http://103.152.112.162:80",
    "http://185.32.6.129:8090",
    "http://103.149.162.194:80",
    "http://103.152.112.157:80",
    "http://185.32.6.131:8090",
]


async def fetch_proxyscrape_proxies(
    protocol: str = "http", timeout: int = 5000, country: str = "all"
) -> List[str]:
    """
    Fetch fresh proxy list from ProxyScrape v4 API.

    Args:
        protocol: 'http', 'socks4', 'socks5'
        timeout: Timeout in milliseconds (1000-10000)
        country: Country code (e.g., 'US', 'GB') or 'all'

    Returns:
        List of proxy URLs
    """
    # Use the v4 API endpoint with JSON format
    api_url = "https://api.proxyscrape.com/v4/free-proxy-list/get"

    params = {
        "request": "display_proxies",
        "proxy_format": "protocolipport",
        "format": "json",
    }

    # Add optional filters
    if protocol != "all":
        params["protocol"] = protocol
    if timeout:
        params["timeout"] = str(timeout)
    if country != "all":
        params["country"] = country

    try:
        logger.info(f"Fetching proxies from ProxyScrape v4: {api_url}")

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                api_url,
                params=params,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; WebScraper/1.0)",
                },
            )

            if response.status_code != 200:
                logger.error(f"ProxyScrape API error: {response.status_code}")
                return []

            data = response.json()

            # Extract proxies from response
            if isinstance(data, dict) and "proxies" in data:
                proxies = []
                for proxy_data in data["proxies"]:
                    if isinstance(proxy_data, dict):
                        protocol = proxy_data.get("protocol", "http")
                        ip = proxy_data.get("ip")
                        port = proxy_data.get("port")
                        if ip and port:
                            proxies.append(f"{protocol}://{ip}:{port}")
                return proxies
            elif isinstance(data, list):
                # Direct list of proxy strings
                return [str(proxy) for proxy in data if proxy]

    except Exception as e:
        logger.error(f"Failed to fetch proxies from ProxyScrape: {e}")
        return []

    return []


async def test_proxy(proxy: str, test_url: str = "http://httpbin.org/ip") -> bool:
    """
    Test if a proxy is working.

    Args:
        proxy: Proxy URL to test
        test_url: URL to test against

    Returns:
        True if proxy is working
    """
    try:
        async with httpx.AsyncClient(
            proxies={"http://": proxy, "https://": proxy}, timeout=10.0
        ) as client:
            response = await client.get(test_url)
            return response.status_code == 200
    except Exception:
        return False


async def get_working_proxies(max_proxies: int = 5, test_count: int = 10) -> List[str]:
    """
    Get a list of working free proxies.

    Args:
        max_proxies: Maximum number of working proxies to return
        test_count: Number of proxies to test from fetched list

    Returns:
        List of working proxy URLs
    """
    # Try to fetch fresh proxies
    fresh_proxies = await fetch_proxyscrape_proxies()

    # Combine with fallback list
    all_proxies = fresh_proxies + FREE_PROXIES

    # Remove duplicates and shuffle
    unique_proxies = list(set(all_proxies))
    random.shuffle(unique_proxies)

    # Test a subset of proxies
    test_proxies = unique_proxies[:test_count]
    working_proxies = []

    logger.info(f"Testing {len(test_proxies)} proxies...")

    for proxy in test_proxies:
        if len(working_proxies) >= max_proxies:
            break

        if await test_proxy(proxy):
            working_proxies.append(proxy)
            logger.info(f"Working proxy found: {proxy}")
        else:
            logger.debug(f"Proxy failed test: {proxy}")

    logger.info(f"Found {len(working_proxies)} working proxies")
    return working_proxies


async def create_proxy_configuration() -> Optional[Dict[str, Any]]:
    """
    Create proxy configuration for Crawlee.

    Returns:
        Proxy configuration dict or None if disabled
    """
    use_proxies = os.getenv("USE_FREE_PROXIES", "false").lower() == "true"

    if not use_proxies:
        logger.info("Proxy usage disabled")
        return None

    working_proxies = await get_working_proxies()

    if not working_proxies:
        logger.warning("No working proxies found, continuing without proxy")
        return None

    # For Crawlee Python, we'll need to return proxy configuration
    # This might need adjustment based on the actual Crawlee Python API
    logger.info(f"Using {len(working_proxies)} proxies")

    return {
        "proxy_urls": working_proxies,
        "use_apify_proxy": False,
    }
