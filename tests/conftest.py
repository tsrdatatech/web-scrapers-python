"""
Pytest configuration and shared fixtures.
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from src.core.base_parser import BaseParser
from src.schemas.news import NewsArticle


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_playwright_page():
    """Create a mock Playwright page object."""
    page = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    page.text_content = AsyncMock(return_value="Sample text")
    page.get_attribute = AsyncMock(return_value="sample-value")
    page.inner_text = AsyncMock(return_value="Inner text")
    page.content = AsyncMock(return_value="<html><body>Content</body></html>")
    page.url = "https://example.com/test"
    return page


@pytest.fixture
def mock_crawlee_request():
    """Create a mock Crawlee request object."""
    request = Mock()
    request.url = "https://example.com/test-article"
    request.loaded_url = "https://example.com/test-article"
    request.user_data = {}
    return request


@pytest.fixture
def mock_context(mock_crawlee_request):
    """Create a mock context for parser testing."""
    return {"request": mock_crawlee_request, "crawler": Mock(), "log": Mock()}


@pytest.fixture
def sample_news_article():
    """Create a sample NewsArticle for testing."""
    return NewsArticle(  # type: ignore
        title="Sample News Article",
        url="https://example.com/news/sample",
        content="This is sample news content for testing purposes.",
        author="Test Author",
    )


@pytest.fixture
def sample_news_data():
    """Create sample news data dictionary."""
    return {
        "title": "Sample Article Title",
        "url": "https://example.com/article",
        "content": "Sample article content goes here.",
        "author": "John Doe",
        "published_at": datetime(2024, 1, 15, 10, 0),
        "description": "A sample article for testing",
        "source": "example.com",
    }


@pytest.fixture
def news_urls():
    """Provide a list of news URLs for testing."""
    return [
        "https://cnn.com/news/breaking-story",
        "https://bbc.com/news/world/article",
        "https://example.com/blog/2024/01/post-title",
        "https://news.site.com/article/important-update",
        "https://journal.com/story/latest-developments",
    ]


@pytest.fixture
def non_news_urls():
    """Provide a list of non-news URLs for testing."""
    return [
        "https://example.com/about",
        "https://shop.com/products/item-123",
        "https://example.com/contact",
        "https://site.com/search?q=query",
        "https://example.com/",
    ]


def create_test_article(**kwargs):
    """Helper function to create test NewsArticle instances."""
    defaults = {"title": "Test Article", "url": "https://example.com/test"}
    defaults.update(kwargs)
    return NewsArticle(**defaults)  # type: ignore


class MockParser(BaseParser):
    """Mock parser class for testing."""

    def __init__(self, parser_id="mock", domains=None, can_parse_result=True):
        self.id = parser_id
        self.domains = domains or []
        self.schema = NewsArticle
        self._can_parse_result = can_parse_result

    async def can_parse(self, url, context=None):
        return self._can_parse_result

    async def parse(self, page, context):
        return create_test_article(title="Mock Article", url=context["request"].url)
