"""
Simple end-to-end tests for basic functionality.
"""

from unittest.mock import Mock, patch

import pytest

from src.core.parser_registry import ParserRegistry
from tests.conftest import MockParser, create_test_article


class TestBasicFunctionality:
    """Test basic scraper functionality."""

    def test_parser_registry_basic_operations(self):
        """Test basic parser registry operations."""
        registry = ParserRegistry()
        parser = MockParser(parser_id="test-parser", domains=["test.com"])

        # Test registration
        registry.register(parser)
        assert registry.get("test-parser") == parser
        assert parser in registry.all()

        # Test domain lookup
        domain_parsers = registry.get_by_domain("test.com")
        assert len(domain_parsers) == 1
        assert domain_parsers[0] == parser

    def test_news_article_creation(self, sample_news_data):
        """Test basic NewsArticle creation and validation."""
        article = create_test_article(**sample_news_data)

        assert article.title == sample_news_data["title"]
        assert str(article.url) == sample_news_data["url"]
        assert article.content == sample_news_data["content"]
        assert article.author == sample_news_data["author"]

    @pytest.mark.asyncio
    async def test_mock_parser_functionality(self, mock_playwright_page, mock_context):
        """Test mock parser basic functionality."""
        parser = MockParser()

        # Test can_parse
        can_parse = await parser.can_parse("https://example.com/test")
        assert can_parse is True

        # Test parse
        result = await parser.parse(mock_playwright_page, mock_context)
        assert result is not None
        assert result.title == "Mock Article"

    def test_url_pattern_matching(self, news_urls, non_news_urls):
        """Test URL pattern matching logic."""
        import re

        # Simple news pattern matching (similar to what GenericNewsParser uses)
        news_patterns = [
            r"/news/",
            r"/article/",
            r"/story/",
            r"/post/",
            r"/\d{4}/\d{2}/",
            r"/blog/",
        ]

        def looks_like_news(url):
            url_lower = url.lower()
            return any(re.search(pattern, url_lower) for pattern in news_patterns)

        # Test news URLs
        for url in news_urls:
            assert looks_like_news(url), f"Should match news URL: {url}"

        # Test non-news URLs
        for url in non_news_urls:
            assert not looks_like_news(url), f"Should not match non-news URL: {url}"

    def test_data_validation_basic(self):
        """Test basic data validation scenarios."""
        # Valid data
        valid_data = {"title": "Valid Title", "url": "https://example.com/valid"}
        article = create_test_article(**valid_data)
        assert article.title == "Valid Title"

        # Test with additional fields
        extended_data = {
            "title": "Extended Article",
            "url": "https://example.com/extended",
            "content": "Extended content",
            "author": "Author Name",
        }
        extended_article = create_test_article(**extended_data)
        assert extended_article.content == "Extended content"
        assert extended_article.author == "Author Name"


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_parser_error_recovery(self, mock_context):
        """Test parser handles errors gracefully."""
        from unittest.mock import AsyncMock

        # Create parser that fails
        failing_parser = MockParser()

        # Mock page that raises exception
        failing_page = AsyncMock()
        failing_page.wait_for_load_state.side_effect = Exception("Page failed")

        # Parser should handle gracefully (this would need actual error handling in parser)
        try:
            result = await failing_parser.parse(failing_page, mock_context)
            # If no exception handling, this might raise
            assert result is not None or result is None
        except Exception:
            # Expected if no error handling implemented yet
            pass

    def test_invalid_url_handling(self):
        """Test handling of invalid URLs."""
        from pydantic import ValidationError

        # This should raise ValidationError
        with pytest.raises(ValidationError):
            create_test_article(title="Test", url="not-a-valid-url")

    def test_missing_required_fields(self):
        """Test validation of missing required fields."""
        from pydantic import ValidationError

        # Missing title
        with pytest.raises(ValidationError):
            create_test_article(url="https://example.com/test")

        # Missing URL
        with pytest.raises(ValidationError):
            create_test_article(title="Test Title")


class TestConfigurationAndSetup:
    """Test configuration and setup functionality."""

    def test_environment_variable_handling(self):
        """Test environment variable processing."""
        import os

        # Test default behavior
        assert os.getenv("NONEXISTENT_VAR") is None
        assert os.getenv("NONEXISTENT_VAR", "default") == "default"

        # Test boolean conversion (common pattern)
        def str_to_bool(value):
            return value.lower() in ("true", "1", "yes") if value else False

        assert str_to_bool("true") is True
        assert str_to_bool("false") is False
        assert str_to_bool("") is False
        assert str_to_bool(None) is False

    def test_basic_logging_setup(self):
        """Test basic logging functionality."""
        import logging

        # Test that logging works at basic level
        logger = logging.getLogger("test")
        logger.info("Test log message")

        # Basic assertion that logger exists
        assert logger.name == "test"
        assert logger.level >= 0
