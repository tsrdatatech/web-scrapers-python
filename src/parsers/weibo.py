"""
Weibo social media parser.
"""

import re
from typing import Any

from playwright.async_api import Page
from pydantic import BaseModel, Field, HttpUrl

from src.core.base_parser import BaseParser
from src.core.logger import logger


class WeiboPost(BaseModel):
    """Schema for Weibo post data."""

    id: str = Field(..., description="Post ID")
    author: str | None = Field(None, description="Post author")
    content: str = Field(..., description="Post content")
    likes: int | None = Field(None, description="Number of likes")
    reposts: int | None = Field(None, description="Number of reposts")
    comments: int | None = Field(None, description="Number of comments")
    url: HttpUrl = Field(..., description="Post URL")


class WeiboParser(BaseParser):
    """Parser for Weibo social media posts."""

    id = "weibo"
    schema = WeiboPost
    domains = ["weibo.com"]

    async def can_parse(self, url: str, context: dict[str, Any] | None = None) -> bool:
        """Check if URL is from Weibo."""
        return "weibo.com" in url.lower()

    async def parse(self, page: Page, context: dict[str, Any]) -> WeiboPost | None:
        """Parse Weibo post from the page."""
        request = context["request"]
        url = request.loaded_url or request.url

        try:
            await page.wait_for_load_state("domcontentloaded")

            # Extract post content
            # (simplified selectors - real Weibo requires more complex handling)
            content = await self._safe_text_content(
                page, "article, .Detail_container__content, .card-comment, body"
            )

            # Extract engagement metrics
            likes = await self._extract_number(
                page, 'span:has-text("赞"), .toolbar_item:has-text("赞")'
            )
            reposts = await self._extract_number(
                page, 'span:has-text("转发"), .toolbar_item:has-text("转发")'
            )
            comments = await self._extract_number(
                page, 'span:has-text("评论"), .toolbar_item:has-text("评论")'
            )

            # Extract author
            author = await self._safe_text_content(
                page, "a:has(img[alt]), .name, .user-name, .author"
            )

            # Create post data
            post_data = {
                "id": request.id or url,
                "author": author,
                "content": content[:10000] if content else "",  # Limit content length
                "likes": likes,
                "reposts": reposts,
                "comments": comments,
                "url": url,
            }

            validated_data = self.validate_data(post_data)
            return validated_data if isinstance(validated_data, WeiboPost) else None

        except Exception as e:
            logger.error(f"Failed to parse Weibo post from {url}: {e}")
            return None

    async def _safe_text_content(self, page: Page, selectors: str) -> str | None:
        """Safely extract text content using multiple selectors."""
        for selector in selectors.split(", "):
            try:
                element = await page.query_selector(selector.strip())
                if element:
                    text = await element.text_content()
                    if text and text.strip():
                        return text.strip()
            except Exception:  # nosec B112: Broad exception for web scraping robustness
                continue
        return None

    async def _extract_number(self, page: Page, selectors: str) -> int | None:
        """Extract and parse numbers from text (likes, comments, etc.)."""
        text = await self._safe_text_content(page, selectors)
        if not text:
            return None

        # Extract numbers from text (handle K, M suffixes)
        match = re.search(r"(\d+(?:[,.]?\d+)*)\s*([KMB万千]?)", text)
        if not match:
            return None

        number_str, suffix = match.groups()
        try:
            # Remove commas and convert to float
            number = float(number_str.replace(",", "").replace(".", ""))

            # Handle suffixes
            if suffix in ["K", "千"]:
                number *= 1000
            elif suffix in ["M", "万"]:
                number *= 10000 if suffix == "万" else 1000000
            elif suffix == "B":
                number *= 1000000000

            return int(number)
        except (ValueError, TypeError):
            return None
