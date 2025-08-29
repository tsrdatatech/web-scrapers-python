"""
AI-enhanced generic news parser with LangChain-powered content analysis.

This parser extends the base GenericNewsParser with advanced AI capabilities
including content summarization, sentiment analysis, and topic classification.
"""

from typing import Any, Dict, Optional
from playwright.async_api import Page

from src.core.base_parser import BaseParser
from src.core.logger import logger
from src.parsers.generic_news import GenericNewsParser
from src.schemas.news import NewsArticle
from src.ai.content_analyzer import create_content_analyzer


class AIEnhancedNewsParser(GenericNewsParser):
    """
    AI-enhanced news parser with LangChain integration.

    Extends the generic news parser with:
    - LangChain-powered content analysis
    - Sentiment analysis and summarization
    - Topic classification and entity extraction
    - Content quality assessment
    """

    id = "ai-enhanced-news"

    def __init__(self, enable_ai_analysis: bool = True):
        """
        Initialize AI-enhanced parser.

        Args:
            enable_ai_analysis: Whether to run AI analysis on extracted content
        """
        super().__init__()
        self.enable_ai_analysis = enable_ai_analysis
        self.content_analyzer = (
            create_content_analyzer(use_mock_llm=True) if enable_ai_analysis else None
        )

    async def parse(self, page: Page, context: Dict[str, Any]) -> Optional[NewsArticle]:
        """
        Parse news article with AI-powered enhancements.

        Args:
            page: Playwright page object
            context: Request context with metadata

        Returns:
            NewsArticle with AI analysis or None if parsing fails
        """
        try:
            # First run the standard parsing
            article = await super().parse(page, context)

            if not article:
                return None

            # Add AI analysis if enabled
            if self.enable_ai_analysis and self.content_analyzer:
                try:
                    logger.info(f"Running AI analysis for: {article.title[:50]}...")

                    # Run LangChain-powered analysis
                    ai_analysis = await self.content_analyzer.analyze_article(article)

                    # Create enhanced article with AI insights
                    enhanced_article = NewsArticle(
                        id=article.id,
                        title=article.title,
                        author=article.author,
                        published_at=article.published_at,
                        url=article.url,
                        description=article.description,
                        content=article.content,
                        image=article.image,
                        source=article.source,
                        ai_analysis=ai_analysis.model_dump(),  # Convert to dict
                    )

                    logger.info(
                        f"AI analysis complete - Sentiment: {ai_analysis.sentiment}, "
                        f"Quality: {ai_analysis.quality_score:.1f}/10, "
                        f"Topics: {', '.join(ai_analysis.topics[:3])}"
                    )

                    return enhanced_article

                except Exception as ai_error:
                    logger.warning(
                        f"AI analysis failed, returning standard article: {ai_error}"
                    )
                    return article

            return article

        except Exception as e:
            logger.error(
                f"AI-enhanced parsing failed for {context.get('request', {}).get('url', 'unknown')}: {e}"
            )
            return None

    async def can_parse(
        self, url: str, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if URL can be parsed with AI enhancements.

        Inherits the same URL pattern matching as GenericNewsParser.
        """
        return await super().can_parse(url, context)


class SmartParserFactory:
    """
    Factory for creating AI-enhanced parsers with different configurations.

    Demonstrates advanced factory pattern with AI configuration options.
    """

    @staticmethod
    def create_enhanced_parser(
        ai_enabled: bool = True,
        sentiment_analysis: bool = True,
        topic_classification: bool = True,
        entity_extraction: bool = True,
    ) -> AIEnhancedNewsParser:
        """
        Create configured AI-enhanced parser.

        Args:
            ai_enabled: Enable AI analysis
            sentiment_analysis: Enable sentiment analysis
            topic_classification: Enable topic classification
            entity_extraction: Enable entity extraction

        Returns:
            Configured AIEnhancedNewsParser
        """
        parser = AIEnhancedNewsParser(enable_ai_analysis=ai_enabled)

        # Could configure specific AI features here
        if parser.content_analyzer:
            logger.info(
                f"Created AI-enhanced parser with features: "
                f"sentiment={sentiment_analysis}, "
                f"topics={topic_classification}, "
                f"entities={entity_extraction}"
            )

        return parser

    @staticmethod
    def create_standard_parser() -> AIEnhancedNewsParser:
        """Create parser without AI enhancements for comparison."""
        return AIEnhancedNewsParser(enable_ai_analysis=False)
