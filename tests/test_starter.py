"""
Starter tests to demonstrate the testing framework.
This file shows basic testing patterns for contributors.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError


class TestProjectSetup:
    """Test basic project setup and imports."""

    def test_pydantic_available(self):
        """Test that Pydantic is available and working."""
        from pydantic import BaseModel, Field

        class TestModel(BaseModel):
            name: str = Field(..., min_length=1)
            value: int = Field(default=0, ge=0)

        # Test valid model
        model = TestModel(name="test", value=42)
        assert model.name == "test"
        assert model.value == 42

        # Test validation
        with pytest.raises(ValidationError):
            TestModel(name="", value=-1)

    def test_datetime_handling(self):
        """Test datetime functionality."""
        now = datetime.now()
        iso_string = now.isoformat()

        assert isinstance(now, datetime)
        assert isinstance(iso_string, str)
        assert "T" in iso_string

    def test_url_pattern_matching(self):
        """Test URL pattern matching logic (used in parsers)."""
        import re

        news_patterns = [
            r"/news/",
            r"/article/",
            r"/story/",
            r"/post/",
            r"/\d{4}/\d{2}/",
            r"/blog/",
        ]

        def is_news_url(url):
            return any(re.search(pattern, url.lower()) for pattern in news_patterns)

        # Test news URLs
        news_urls = [
            "https://example.com/news/breaking",
            "https://site.com/article/123",
            "https://blog.com/2024/01/post",
            "https://news.com/story/update",
        ]

        for url in news_urls:
            assert is_news_url(url), f"Should match: {url}"

        # Test non-news URLs
        non_news = ["https://example.com/about", "https://shop.com/products/item"]

        for url in non_news:
            assert not is_news_url(url), f"Should not match: {url}"


class TestNewsSchemaIntegration:
    """Test NewsArticle schema integration."""

    def test_news_article_import(self):
        """Test that NewsArticle can be imported."""
        try:
            from src.schemas.news import NewsArticle

            assert NewsArticle is not None
        except ImportError:
            pytest.skip("NewsArticle schema not available - install dependencies")

    def test_news_article_basic_usage(self):
        """Test basic NewsArticle usage if available."""
        try:
            from src.schemas.news import NewsArticle

            # Test minimal article
            article = NewsArticle(  # type: ignore
                title="Test Article", url="https://example.com/test"
            )

            assert article.title == "Test Article"
            assert str(article.url) == "https://example.com/test"
            assert article.content is None
            assert article.author is None

        except ImportError:
            pytest.skip("NewsArticle schema not available")


class TestContributionWorkflow:
    """Test patterns that contributors should follow."""

    def test_async_function_pattern(self):
        """Test async function patterns used in parsers."""

        async def sample_parser_method(url: str) -> bool:
            """Sample async method like can_parse."""
            return "example.com" in url

        # Test async execution
        import asyncio

        async def run_test():
            result1 = await sample_parser_method("https://example.com/article")
            result2 = await sample_parser_method("https://other.com/page")
            return result1, result2

        results = asyncio.run(run_test())
        assert results[0] is True
        assert results[1] is False

    def test_mock_usage_pattern(self):
        """Test mock usage patterns for testing parsers."""
        from unittest.mock import AsyncMock, Mock

        # Create mock page (like Playwright page)
        mock_page = AsyncMock()
        mock_page.text_content.return_value = "Sample Title"
        mock_page.url = "https://example.com/test"

        # Create mock context
        mock_request = Mock()
        mock_request.url = "https://example.com/test"
        mock_context = {"request": mock_request}

        # Verify mocks work
        assert mock_page.url == "https://example.com/test"
        assert mock_context["request"].url == "https://example.com/test"

    def test_error_handling_pattern(self):
        """Test error handling patterns."""

        def safe_parse_int(value: str) -> int:
            """Example of safe parsing with error handling."""
            try:
                return int(value)
            except (ValueError, TypeError):
                return 0

        # Test successful parsing
        assert safe_parse_int("42") == 42

        # Test error handling
        assert safe_parse_int("not-a-number") == 0
        assert safe_parse_int("") == 0
        assert safe_parse_int(None) == 0  # type: ignore

    def test_data_validation_pattern(self):
        """Test data validation patterns used in parsers."""

        def validate_url(url: str) -> bool:
            """Simple URL validation."""
            if not url or not isinstance(url, str):
                return False
            return url.startswith(("http://", "https://"))

        # Test valid URLs
        assert validate_url("https://example.com") is True
        assert validate_url("http://test.com") is True

        # Test invalid URLs
        assert validate_url("not-a-url") is False
        assert validate_url("") is False
        assert validate_url(None) is False  # type: ignore
        assert validate_url("ftp://example.com") is False


@pytest.mark.asyncio
async def test_async_pytest_setup():
    """Test that async pytest is working."""

    async def sample_async_operation():
        return "async result"

    result = await sample_async_operation()
    assert result == "async result"


def test_project_structure():
    """Test that project structure is as expected."""
    import os

    # Check that we're in the right directory
    assert os.path.exists("src"), "src directory should exist"
    assert os.path.exists("tests"), "tests directory should exist"
    assert os.path.exists("README.md"), "README.md should exist"
    assert os.path.exists("LICENSE"), "LICENSE should exist"

    # Check key source files exist
    src_files = [
        "src/__init__.py",
        "src/main.py",
        "src/core/base_parser.py",
        "src/schemas/news.py",
    ]

    for file_path in src_files:
        assert os.path.exists(file_path), f"{file_path} should exist"


if __name__ == "__main__":
    # Allow running this file directly for quick testing
    pytest.main([__file__, "-v"])
