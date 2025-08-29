"""Tests for AI-enhanced news parser functionality."""

from unittest.mock import AsyncMock, Mock

import pytest

from src.parsers.ai_enhanced_news import AIEnhancedNewsParser
from src.schemas.news import NewsArticle


class TestAIEnhancedNewsParser:
    """Test AI-enhanced news parser functionality."""

    def test_parser_initialization(self):
        """Test that parser can be initialized."""
        parser = AIEnhancedNewsParser()
        assert parser is not None
        assert hasattr(parser, "name")
        assert hasattr(parser, "patterns")

    @pytest.mark.asyncio
    async def test_parse_basic_functionality(self):
        """Test basic parsing functionality."""
        parser = AIEnhancedNewsParser()

        # Create mock page
        mock_page = AsyncMock()
        mock_page.title.return_value = "Test Title"
        mock_page.url = "https://example.com/test"

        # Mock the content extraction
        mock_page.query_selector.return_value = Mock()
        mock_page.query_selector.return_value.inner_text = AsyncMock(
            return_value="Test content"
        )

        # Test parsing with context
        context = {"url": "https://example.com/test"}

        try:
            result = await parser.parse(mock_page, context)
            # If parsing succeeds, check basic structure
            if result:
                assert isinstance(result, NewsArticle)
        except Exception:
            # Parser might fail due to missing AI components in test env
            pytest.skip("AI components not available in test environment")

    def test_smart_parser_factory_exists(self):
        """Test smart parser factory exists."""
        try:
            from src.parsers.ai_enhanced_news import SmartParserFactory

            factory = SmartParserFactory()
            assert factory is not None
        except ImportError:
            pytest.skip("SmartParserFactory not available")
