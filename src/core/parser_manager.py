"""
Parser manager for intelligent parser selection.
"""

from typing import Optional
import httpx
from urllib.parse import urlparse

from .base_parser import BaseParser
from .parser_registry import ParserRegistry
from .logger import logger


class ParserManager:
    """Manages parser selection logic."""
    
    def __init__(self, registry: ParserRegistry) -> None:
        self.registry = registry
    
    async def select_parser(
        self, 
        url: str, 
        forced_id: Optional[str] = None,
        context: Optional[dict] = None
    ) -> Optional[BaseParser]:
        """
        Select the most appropriate parser for a given URL.
        
        Args:
            url: The URL to parse
            forced_id: Force a specific parser ID
            context: Additional context for parser selection
            
        Returns:
            Selected parser instance or None
        """
        # If a specific parser is requested, use it
        if forced_id:
            forced_parser = self.registry.get(forced_id)
            if not forced_parser:
                logger.warning(f"Forced parser '{forced_id}' not found")
            return forced_parser
        
        # Try each parser's can_parse method
        for parser in self.registry.all():
            try:
                if await parser.can_parse(url, context):
                    logger.info(f"Selected parser '{parser.id}' for URL: {url}")
                    return parser
            except Exception as e:
                logger.warning(f"Error in {parser.id}.can_parse(): {e}")
        
        # Fallback: try generic news parser for news-like URLs
        generic_parser = self.registry.get("generic-news")
        if generic_parser:
            try:
                # Simple heuristic: check if URL looks like news content
                if await self._looks_like_news(url):
                    logger.info(f"Fallback to generic-news parser for: {url}")
                    return generic_parser
            except Exception as e:
                logger.debug(f"Generic news fallback failed: {e}")
        
        logger.debug(f"No suitable parser found for: {url}")
        return None
    
    async def _looks_like_news(self, url: str) -> bool:
        """
        Simple heuristic to determine if a URL might be a news article.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL appears to be news content
        """
        # Check URL patterns
        news_patterns = [
            "news", "article", "story", "post", "blog", 
            "/20", "/article/", "/news/", "/story/"
        ]
        
        url_lower = url.lower()
        if any(pattern in url_lower for pattern in news_patterns):
            return True
        
        # Try to fetch and check for article indicators
        try:
            if httpx:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.head(url, follow_redirects=True)
                    content_type = response.headers.get("content-type", "")
                    
                    # Basic content type check
                    if "text/html" in content_type:
                        return True
            else:
                # If httpx not available, assume it might be news
                return True
                    
        except Exception:
            # If we can't check, assume it might be news
            return True
        
        return False
