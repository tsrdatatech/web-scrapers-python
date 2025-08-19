"""
Tests for the GenericNewsParser.
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from pydantic import ValidationError

from src.parsers.generic_news import GenericNewsParser
from src.schemas.news import NewsArticle


class TestGenericNewsParser:
    """Test cases for GenericNewsParser."""

    @pytest.fixture
    def parser(self):
        """Create a GenericNewsParser instance."""
        return GenericNewsParser()

    @pytest.fixture
    def mock_page(self):
        """Create a mock Playwright page."""
        page = AsyncMock()
        page.wait_for_load_state = AsyncMock()
        page.text_content = AsyncMock()
        page.get_attribute = AsyncMock()
        page.inner_text = AsyncMock()
        page.content = AsyncMock(return_value="<html><body>Test content</body></html>")
        return page

    @pytest.fixture
    def mock_context(self):
        """Create a mock context."""
        request = Mock()
        request.url = "https://example.com/news/test-article"
        request.loaded_url = "https://example.com/news/test-article"

        return {"request": request, "crawler": Mock(), "log": Mock()}

    @pytest.mark.asyncio
    async def test_can_parse_news_urls(self, parser):
        """Test that parser correctly identifies news URLs."""
        news_urls = [
            "https://example.com/news/breaking-story",
            "https://site.com/article/2024/01/15/story",
            "https://blog.com/2024/02/post-title",
            "https://news.com/story/important-news",
            "https://example.com/blog/my-post",
        ]

        for url in news_urls:
            result = await parser.can_parse(url)
            assert result is True, f"Should parse news URL: {url}"

    @pytest.mark.asyncio
    async def test_cannot_parse_non_news_urls(self, parser):
        """Test that parser rejects non-news URLs."""
        non_news_urls = [
            "https://example.com/about",
            "https://site.com/contact",
            "https://shop.com/products/item",
            "https://example.com/",
            "https://site.com/search?q=test",
        ]

        for url in non_news_urls:
            result = await parser.can_parse(url)
            assert result is False, f"Should not parse non-news URL: {url}"

    @pytest.mark.asyncio
    async def test_parse_basic_content(self, parser, mock_page, mock_context):
        """Test basic content extraction."""
        # Setup mock page responses
        mock_page.text_content.side_effect = [
            "Test Article Title",  # h1
            "Test content here",  # article, main, or .content
            "Test Author",  # author selector
            "2024-01-15",  # time or date selector
        ]

        mock_page.get_attribute.return_value = "2024-01-15T10:00:00Z"

        # Mock the extraction methods to return basic data
        with patch.object(
            parser,
            "_extract_with_multiple_methods",
            return_value={
                "title": "Test Article Title",
                "content": "Test content here",
                "author": "Test Author",
                "published_at": datetime(2024, 1, 15, 10, 0),
            },
        ):

            result = await parser.parse(mock_page, mock_context)

            assert isinstance(result, NewsArticle)
            assert result.title == "Test Article Title"
            assert result.content == "Test content here"
            assert result.author == "Test Author"
            assert result.url == "https://example.com/news/test-article"

    @pytest.mark.asyncio
    async def test_parse_with_fallback(self, parser, mock_page, mock_context):
        """Test fallback content extraction when main methods fail."""
        # Setup mock to simulate failed extraction that needs fallback
        mock_page.text_content.side_effect = [
            "Fallback Title",  # title fallback
            "Fallback content",  # content fallback
        ]

        with (
            patch.object(
                parser, "_extract_with_multiple_methods", return_value={"title": ""}
            ),
            patch.object(
                parser,
                "_extract_basic_content",
                return_value={"title": "Fallback Title", "content": "Fallback content"},
            ),
        ):

            result = await parser.parse(mock_page, mock_context)

            assert isinstance(result, NewsArticle)
            assert result.title == "Fallback Title"
            assert result.content == "Fallback content"

    @pytest.mark.asyncio
    async def test_parse_returns_none_on_failure(self, parser, mock_page, mock_context):
        """Test that parser returns None when extraction completely fails."""
        # Mock all extraction methods to fail
        with (
            patch.object(parser, "_extract_with_multiple_methods", return_value={}),
            patch.object(parser, "_extract_basic_content", return_value={}),
        ):

            result = await parser.parse(mock_page, mock_context)
            assert result is None

    @pytest.mark.asyncio
    async def test_parse_handles_exceptions(self, parser, mock_page, mock_context):
        """Test that parser gracefully handles exceptions."""
        # Make page methods raise exceptions
        mock_page.wait_for_load_state.side_effect = Exception("Page load failed")

        result = await parser.parse(mock_page, mock_context)
        assert result is None

    def test_parser_id_and_schema(self, parser):
        """Test parser has correct ID and schema."""
        assert parser.id == "generic-news"
        assert parser.schema == NewsArticle
        assert parser.domains == []  # Generic parser has no specific domains

    @pytest.mark.asyncio
    async def test_extract_date_formats(self, parser):
        """Test date extraction handles various formats."""
        test_cases = [
            ("2024-01-15T10:00:00Z", datetime(2024, 1, 15, 10, 0)),
            ("2024-01-15", datetime(2024, 1, 15)),
            ("January 15, 2024", datetime(2024, 1, 15)),
            ("15 Jan 2024", datetime(2024, 1, 15)),
            ("invalid-date", None),
        ]

        for date_str, expected in test_cases:
            result = await parser._parse_date(date_str)
            if expected:
                assert result.date() == expected.date()
            else:
                assert result is None
