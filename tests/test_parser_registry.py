"""
Tests for parser registry functionality.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from src.core.base_parser import BaseParser
from src.core.parser_registry import ParserRegistry, create_parser_registry


class MockParser(BaseParser):
    """Mock parser for testing."""

    id = "mock-parser"
    domains = ["example.com"]

    async def can_parse(self, url, context=None):
        return "example.com" in url

    async def parse(self, page, context):
        return {"title": "Mock Article", "url": url}


class TestParserRegistry:
    """Test cases for ParserRegistry."""

    def test_register_parser(self):
        """Test parser registration."""
        registry = ParserRegistry()
        parser = MockParser()

        registry.register(parser)

        assert registry.get("mock-parser") == parser
        assert parser in registry.all()

    def test_get_nonexistent_parser(self):
        """Test getting a parser that doesn't exist."""
        registry = ParserRegistry()

        assert registry.get("nonexistent") is None

    def test_get_by_domain(self):
        """Test getting parsers by domain."""
        registry = ParserRegistry()
        parser = MockParser()
        registry.register(parser)

        domain_parsers = registry.get_by_domain("example.com")
        assert len(domain_parsers) == 1
        assert domain_parsers[0] == parser

        # Test non-matching domain
        domain_parsers = registry.get_by_domain("other.com")
        assert len(domain_parsers) == 0


@pytest.mark.asyncio
async def test_create_parser_registry():
    """Test parser registry creation and auto-discovery."""
    # This is a basic test - in practice would require test parsers
    registry = await create_parser_registry()
    assert isinstance(registry, ParserRegistry)
