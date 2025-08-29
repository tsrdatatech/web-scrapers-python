"""
Tests for the BaseParser abstract class and parser functionality.
"""

from unittest.mock import AsyncMock, Mock

import pytest
from pydantic import BaseModel, ValidationError

from src.core.base_parser import BaseParser
from src.schemas.news import NewsArticle


class TestSchema(BaseModel):
    """Test schema for parser testing."""

    title: str
    content: str


class ConcreteParser(BaseParser):
    """Concrete implementation of BaseParser for testing."""

    id = "test-parser"
    schema = TestSchema
    domains = ["test.com"]

    async def can_parse(self, url, context=None):
        return "test.com" in url

    async def parse(self, page, context):
        return TestSchema(title="Test Title", content="Test Content")


class InvalidParser(BaseParser):
    """Parser without required method implementations."""

    id = "invalid-parser"
    schema = TestSchema


class TestBaseParser:
    """Test cases for BaseParser."""

    def test_base_parser_is_abstract(self):
        """Test that BaseParser cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseParser()  # type: ignore

    def test_concrete_parser_creation(self):
        """Test that concrete parser can be created."""
        parser = ConcreteParser()
        assert parser.id == "test-parser"
        assert parser.schema == TestSchema
        assert parser.domains == ["test.com"]

    @pytest.mark.asyncio
    async def test_concrete_parser_can_parse(self):
        """Test can_parse method in concrete parser."""
        parser = ConcreteParser()

        assert await parser.can_parse("https://test.com/article") is True
        assert await parser.can_parse("https://other.com/article") is False

    @pytest.mark.asyncio
    async def test_concrete_parser_parse(self):
        """Test parse method in concrete parser."""
        parser = ConcreteParser()
        mock_page = AsyncMock()
        mock_context = {"request": Mock()}

        result = await parser.parse(mock_page, mock_context)

        assert isinstance(result, TestSchema)
        assert result.title == "Test Title"
        assert result.content == "Test Content"

    def test_invalid_parser_creation_fails(self):
        """Test that parser without required methods cannot be instantiated."""
        with pytest.raises(TypeError):
            InvalidParser()  # type: ignore

    def test_validate_data_success(self):
        """Test successful data validation."""
        parser = ConcreteParser()
        data = {"title": "Valid Title", "content": "Valid Content"}

        result = parser.validate_data(data)

        assert isinstance(result, TestSchema)
        assert result.title == "Valid Title"
        assert result.content == "Valid Content"

    def test_validate_data_failure(self):
        """Test data validation failure."""
        parser = ConcreteParser()
        invalid_data = {"title": "Missing content field"}

        with pytest.raises(ValidationError):
            parser.validate_data(invalid_data)

    def test_validate_data_with_none_schema(self):
        """Test validation when schema is None."""

        class NoSchemaParser(BaseParser):
            id = "no-schema"
            schema = None

            async def can_parse(self, url, context=None):
                return True

            async def parse(self, page, context):
                return {"raw": "data"}

        parser = NoSchemaParser()
        data = {"any": "data"}

        # Should return data as-is when no schema
        result = parser.validate_data(data)
        assert result == data


class TestParserWithNewsSchema:
    """Test parser using the actual NewsArticle schema."""

    class NewsParser(BaseParser):
        """Test parser using NewsArticle schema."""

        id = "news-test"
        schema = NewsArticle
        domains = ["news.test.com"]

        async def can_parse(self, url, context=None):
            return "news.test.com" in url

        async def parse(self, page, context):
            # Create with required fields only
            return NewsArticle(  # type: ignore
                title="News Title",
                url="https://news.test.com/article",
                content="News content here",
            )

    @pytest.mark.asyncio
    async def test_news_parser_integration(self):
        """Test parser with NewsArticle schema."""
        parser = self.NewsParser()
        mock_page = AsyncMock()
        mock_context = {"request": Mock()}

        result = await parser.parse(mock_page, mock_context)

        assert isinstance(result, NewsArticle)
        assert result.title == "News Title"
        assert str(result.url) == "https://news.test.com/article"
        assert result.content == "News content here"

    def test_news_schema_validation(self):
        """Test NewsArticle schema validation in parser."""
        parser = self.NewsParser()

        # Valid data
        valid_data = {"title": "Valid News", "url": "https://news.test.com/valid"}
        result = parser.validate_data(valid_data)
        assert isinstance(result, NewsArticle)

        # Invalid data (missing required fields)
        invalid_data = {"content": "Missing title and URL"}
        with pytest.raises(ValidationError):
            parser.validate_data(invalid_data)


class TestParserDomainHandling:
    """Test domain-related functionality."""

    class MultiDomainParser(BaseParser):
        """Parser that handles multiple domains."""

        id = "multi-domain"
        schema = TestSchema
        domains = ["example.com", "test.com", "demo.org"]

        async def can_parse(self, url, context=None):
            return any(domain in url for domain in self.domains)

        async def parse(self, page, context):
            return TestSchema(title="Multi Domain", content="Content")

    @pytest.mark.asyncio
    async def test_multi_domain_parsing(self):
        """Test parser with multiple domains."""
        parser = self.MultiDomainParser()

        # Test each domain
        test_urls = [
            "https://example.com/article",
            "https://test.com/news",
            "https://demo.org/post",
        ]

        for url in test_urls:
            assert await parser.can_parse(url) is True

        # Test non-matching domain
        assert await parser.can_parse("https://other.com/article") is False

    def test_empty_domains_list(self):
        """Test parser with empty domains list."""

        class NoDomainParser(BaseParser):
            id = "no-domain"
            schema = TestSchema
            domains = []

            async def can_parse(self, url, context=None):
                return True  # Accept any URL

            async def parse(self, page, context):
                return TestSchema(title="Any Domain", content="Content")

        parser = NoDomainParser()
        assert parser.domains == []
