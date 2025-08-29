"""
Tests for the NewsArticle schema and validation.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.schemas.news import NewsArticle


class TestNewsArticle:
    """Test cases for NewsArticle schema."""

    def test_valid_article_creation(self):
        """Test creating a valid NewsArticle."""
        article_data = {
            "title": "Test Article",
            "url": "https://example.com/article",
            "content": "This is test content",
            "author": "John Doe",
            "published_at": datetime(2024, 1, 15, 10, 0),
            "description": "Test description",
            "source": "Example News",
        }

        article = NewsArticle(**article_data)

        assert article.title == "Test Article"
        assert str(article.url) == "https://example.com/article"
        assert article.content == "This is test content"
        assert article.author == "John Doe"
        assert article.published_at == datetime(2024, 1, 15, 10, 0)
        assert article.description == "Test description"
        assert article.source == "Example News"

    def test_minimal_valid_article(self):
        """Test creating article with only required fields."""
        article = NewsArticle(  # type: ignore
            title="Minimal Article", url="https://example.com/minimal"
        )

        assert article.title == "Minimal Article"
        assert str(article.url) == "https://example.com/minimal"
        assert article.content is None
        assert article.author is None
        assert article.published_at is None
        assert article.description is None
        assert article.source is None
        assert article.id is None
        assert article.image is None

    def test_missing_required_title(self):
        """Test that missing title raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            NewsArticle(url="https://example.com/article")  # type: ignore

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("title",)
        assert errors[0]["type"] == "missing"

    def test_missing_required_url(self):
        """Test that missing URL raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            NewsArticle(title="Test Article")  # type: ignore

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("url",)
        assert errors[0]["type"] == "missing"

    def test_invalid_url_format(self):
        """Test that invalid URL format raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            NewsArticle(title="Test Article", url="not-a-valid-url")  # type: ignore

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("url",)
        assert "url" in errors[0]["type"]

    def test_invalid_image_url(self):
        """Test that invalid image URL raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            NewsArticle(  # type: ignore
                title="Test Article",
                url="https://example.com/article",
                image="not-a-valid-url",
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("image",)

    def test_valid_image_url(self):
        """Test that valid image URL is accepted."""
        article = NewsArticle(  # type: ignore
            title="Test Article",
            url="https://example.com/article",
            image="https://example.com/image.jpg",
        )

        assert str(article.image) == "https://example.com/image.jpg"

    def test_datetime_serialization(self):
        """Test that datetime fields are properly serialized."""
        article = NewsArticle(  # type: ignore
            title="Test Article",
            url="https://example.com/article",
            published_at=datetime(2024, 1, 15, 10, 30, 45),
        )

        # Test JSON serialization
        json_data = article.model_dump(mode="json")
        assert json_data["published_at"] == "2024-01-15T10:30:45"

    def test_article_with_all_fields(self):
        """Test article creation with all possible fields."""
        article_data = {
            "id": "article-123",
            "title": "Complete Test Article",
            "author": "Jane Smith",
            "published_at": datetime(2024, 1, 15, 14, 30),
            "url": "https://news.example.com/complete-article",
            "description": "A comprehensive test article with all fields populated",
            "content": "This is the full content of the test article...",
            "image": "https://news.example.com/images/article.jpg",
            "source": "Example News Network",
        }

        article = NewsArticle(**article_data)

        # Verify all fields are set correctly
        for field, value in article_data.items():
            if field in ["url", "image"]:
                assert str(getattr(article, field)) == str(value)
            else:
                assert getattr(article, field) == value

    def test_empty_string_fields(self):
        """Test behavior with empty string fields."""
        article = NewsArticle(  # type: ignore
            title="",  # Empty but not None
            url="https://example.com/article",
            content="",
            author="",
            description="",
        )

        assert article.title == ""
        assert article.content == ""
        assert article.author == ""
        assert article.description == ""

    def test_none_vs_empty_string(self):
        """Test distinction between None and empty string."""
        article = NewsArticle(  # type: ignore
            title="Test", url="https://example.com/article", content=None, author=""
        )

        assert article.content is None
        assert article.author == ""

    def test_url_normalization(self):
        """Test URL normalization and validation."""
        test_urls = [
            "https://example.com/article",
            "http://example.com/article",
            "https://subdomain.example.com/path/to/article",
            "https://example.com/article?param=value",
            "https://example.com/article#section",
        ]

        for url in test_urls:
            article = NewsArticle(title="Test", url=url)  # type: ignore
            assert str(article.url) == url
