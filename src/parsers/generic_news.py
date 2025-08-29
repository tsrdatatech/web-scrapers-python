"""
Generic news parser using article extraction libraries.
"""

import re
from datetime import datetime
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import newspaper
import trafilatura
from playwright.async_api import Page

from src.core.base_parser import BaseParser
from src.core.logger import logger
from src.schemas.news import NewsArticle


class GenericNewsParser(BaseParser):
    """Generic parser for news articles using multiple extraction methods."""

    id = "generic-news"
    schema = NewsArticle

    async def can_parse(
        self, url: str, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if URL looks like a news article."""
        # Simple heuristic based on URL patterns
        news_patterns = [
            r"/news/",
            r"/article/",
            r"/story/",
            r"/post/",
            r"/\d{4}/\d{2}/",
            r"/blog/",
            r"/(news|article|story)",
        ]

        url_lower = url.lower()
        return any(re.search(pattern, url_lower) for pattern in news_patterns)

    async def parse(self, page: Page, context: Dict[str, Any]) -> Optional[NewsArticle]:
        """Parse news article from the page."""
        request = context["request"]
        url = request.loaded_url or request.url

        try:
            await page.wait_for_load_state("domcontentloaded")

            # Try multiple extraction methods
            article_data = await self._extract_with_multiple_methods(page, url)

            # Fallback to basic page scraping if needed
            if not article_data.get("title"):
                article_data.update(await self._extract_basic_content(page))

            # Clean and validate data
            cleaned_data = self._clean_article_data(article_data, url)

            # Validate and return
            validated_data = self.validate_data(cleaned_data)
            if validated_data:
                return NewsArticle(**validated_data.model_dump())
            return None

        except Exception as e:
            logger.error(f"Failed to parse article from {url}: {e}")
            return None

    async def _extract_with_multiple_methods(
        self, page: Page, url: str
    ) -> Dict[str, Any]:
        """Extract article using multiple methods and combine results."""
        article_data = {}

        # Method 1: Trafilatura (fastest, good for content)
        try:
            html_content = await page.content()
            extracted = trafilatura.extract_metadata(html_content)
            if extracted:
                article_data.update(
                    {
                        "title": getattr(extracted, "title", None),
                        "author": getattr(extracted, "author", None),
                        "description": getattr(extracted, "description", None),
                        "published_at": self._parse_date(
                            getattr(extracted, "date", None)
                        ),
                        "content": trafilatura.extract(
                            html_content, include_comments=False
                        ),
                    }
                )
        except Exception as e:
            logger.debug(f"Trafilatura extraction failed: {e}")

        # Method 2: Newspaper3k (good for metadata)
        try:
            article = newspaper.Article(url)
            article.set_html(await page.content())
            article.parse()

            # Only override if we don't have data or if newspaper has better data
            if not article_data.get("title") and article.title:
                article_data["title"] = article.title
            if not article_data.get("content") and article.text:
                article_data["content"] = article.text
            if not article_data.get("author") and article.authors:
                article_data["author"] = ", ".join(article.authors)
            if not article_data.get("published_at") and article.publish_date:
                article_data["published_at"] = article.publish_date
            if not article_data.get("image") and article.top_image:
                article_data["image"] = article.top_image

        except Exception as e:
            logger.debug(f"Newspaper3k extraction failed: {e}")

        return article_data

    async def _extract_basic_content(self, page: Page) -> Dict[str, Any]:
        """Extract basic content using CSS selectors as fallback."""
        data = {}

        try:
            # Try common title selectors
            title_selectors = ["h1", "title", ".article-title", ".post-title"]
            for selector in title_selectors:
                try:
                    title = await page.text_content(selector)
                    if title and title.strip():
                        data["title"] = title.strip()
                        break
                except (
                    Exception
                ):  # nosec B112: Broad exception for web scraping robustness
                    continue

            # Try common content selectors
            content_selectors = [
                "article",
                ".article-content",
                ".post-content",
                "main",
                ".content",
                "body",
            ]
            for selector in content_selectors:
                try:
                    content = await page.text_content(selector)
                    if (
                        content and len(content.strip()) > 100
                    ):  # Reasonable content length
                        data["content"] = content.strip()[
                            :10000
                        ]  # Limit content length
                        break
                except (
                    Exception
                ):  # nosec B112: Broad exception for web scraping robustness
                    continue

            # Try to get page title if no article title found
            if not data.get("title"):
                page_title = await page.title()
                if page_title:
                    data["title"] = page_title

        except Exception as e:
            logger.debug(f"Basic extraction failed: {e}")

        return data

    def _clean_article_data(self, data: Dict[str, Any], url: str) -> Dict[str, Any]:
        """Clean and normalize extracted article data."""
        cleaned: Dict[str, Any] = {
            "url": url,
            "source": urlparse(url).netloc,
        }

        # Clean title
        if data.get("title"):
            title = str(data["title"]).strip()
            # Remove common title suffixes
            title = re.sub(r"\s*[-|]\s*.+$", "", title)
            cleaned["title"] = title

        # Clean content
        if data.get("content"):
            content = str(data["content"]).strip()
            # Remove excessive whitespace
            content = re.sub(r"\s+", " ", content)
            cleaned["content"] = content[:10000]  # Limit length

        # Clean author
        if data.get("author"):
            author = str(data["author"]).strip()
            if len(author) < 100:  # Reasonable author name length
                cleaned["author"] = author

        # Clean description
        if data.get("description"):
            description = str(data["description"]).strip()
            if len(description) < 1000:  # Reasonable description length
                cleaned["description"] = description

        # Handle published date
        if data.get("published_at"):
            parsed_date = self._parse_date(data["published_at"])
            if parsed_date:
                cleaned["published_at"] = parsed_date

        # Handle image URL
        if data.get("image"):
            image_url = str(data["image"]).strip()
            if image_url.startswith(("http://", "https://")):
                cleaned["image"] = image_url

        return cleaned

    def _parse_date(self, date_value: Any) -> Optional[datetime]:
        """Parse various date formats into datetime object."""
        if not date_value:
            return None

        if isinstance(date_value, datetime):
            return date_value

        if isinstance(date_value, str):
            # Try common date formats
            date_formats = [
                "%Y-%m-%d",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%d %H:%M:%S",
                "%d/%m/%Y",
                "%m/%d/%Y",
            ]

            for fmt in date_formats:
                try:
                    return datetime.strptime(date_value.strip(), fmt)
                except ValueError:
                    continue

        return None
