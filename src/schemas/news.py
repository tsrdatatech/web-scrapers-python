"""
Pydantic schemas for news articles and related data structures.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class NewsArticle(BaseModel):
    """Schema for news article data."""

    id: str | None = Field(None, description="Unique identifier for the article")
    title: str = Field(..., description="Article title")
    author: str | None = Field(None, description="Article author")
    published_at: datetime | None = Field(None, description="Publication date")
    url: HttpUrl = Field(..., description="Article URL")
    description: str | None = Field(None, description="Article description/summary")
    content: str | None = Field(None, description="Full article content")
    image: HttpUrl | None = Field(None, description="Featured image URL")
    source: str | None = Field(None, description="Source domain/publication")

    # AI Analysis Results (Optional) - stored as dict to avoid circular imports
    ai_analysis: dict[str, Any] | None = Field(
        None, description="AI-powered content analysis results"
    )

    class Config:
        """Pydantic model configuration."""

        json_encoders = {datetime: lambda v: v.isoformat() if v else None}

        # Example data for documentation
        schema_extra = {
            "example": {
                "id": "article_123",
                "title": "Breaking News: Important Event Happens",
                "author": "Jane Doe",
                "published_at": "2024-01-15T10:30:00Z",
                "url": "https://example.com/news/breaking-news",
                "description": "This is a brief summary of the important event.",
                "content": "Full article content goes here...",
                "image": "https://example.com/images/news.jpg",
                "source": "example.com",
            }
        }
