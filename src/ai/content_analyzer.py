"""
AI-powered content analysis using LangChain for extracted articles.

This module demonstrates advanced LangChain integration for:
- Article summarization and sentiment analysis
- Content quality assessment
- Topic classification and entity extraction
- Language detection and readability scoring
"""

import re
from datetime import datetime
from typing import Any

try:
    from langchain_community.llms import FakeListLLM
    from langchain_core.prompts import PromptTemplate

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

from pydantic import BaseModel, Field

from src.core.logger import logger
from src.schemas.news import NewsArticle


class ContentAnalysis(BaseModel):
    """Schema for AI-powered content analysis results."""

    # Core Analysis
    summary: str = Field(..., description="Concise article summary (2-3 sentences)")
    sentiment: str = Field(
        ..., description="Article sentiment: positive, negative, neutral, mixed"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Analysis confidence score"
    )

    # Content Quality
    quality_score: float = Field(
        ..., ge=0.0, le=10.0, description="Content quality score (0-10)"
    )
    readability: str = Field(
        ..., description="Readability level: basic, intermediate, advanced"
    )
    completeness: float = Field(
        ..., ge=0.0, le=1.0, description="Content completeness score"
    )

    # Classification
    topics: list[str] = Field(
        default_factory=list, description="Main article topics/categories"
    )
    entities: list[str] = Field(
        default_factory=list, description="Key entities (people, orgs, places)"
    )
    language: str = Field(default="en", description="Detected language code")

    # Metadata
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    word_count: int = Field(default=0, description="Article word count")

    class Config:
        schema_extra = {
            "example": {
                "summary": "Breaking news about a major technology advancement.",
                "sentiment": "positive",
                "confidence": 0.87,
                "quality_score": 8.2,
                "readability": "intermediate",
                "completeness": 0.93,
                "topics": ["technology", "artificial intelligence", "innovation"],
                "entities": ["OpenAI", "Sam Altman", "Silicon Valley"],
                "language": "en",
                "word_count": 1247,
            }
        }


class AdvancedContentAnalyzer:
    """
    LangChain-powered content analyzer for web scraped articles.

    Provides sophisticated content analysis capabilities using local LLM models
    to demonstrate AI/ML engineering expertise without external API dependencies.
    """

    def __init__(self, use_mock_llm: bool = True):
        """
        Initialize the content analyzer.

        Args:
            use_mock_llm: Whether to use mock LLM responses for demonstration
        """
        self.use_mock_llm = use_mock_llm
        self._setup_llm()
        self._setup_parsers()

    def _setup_llm(self) -> None:
        """Setup LLM for content analysis."""
        if not LANGCHAIN_AVAILABLE:
            logger.warning("LangChain not available - using fallback analysis")
            self.llm = None
            return

        if self.use_mock_llm:
            # Use mock responses for portfolio demonstration
            mock_responses = [
                # Summary response
                (
                    "This article discusses a major breakthrough in artificial "
                    "intelligence technology that could revolutionize various "
                    "industries. The development represents a significant step "
                    "forward in machine learning capabilities."
                ),
                # Sentiment analysis
                "positive",
                # Topic classification
                (
                    "technology, artificial intelligence, innovation, "
                    "machine learning, breakthrough"
                ),
                # Entity extraction
                "OpenAI, GPT-4, Sam Altman, Silicon Valley, Stanford University",
                # Quality assessment
                "8.5",
            ]
            self.llm = FakeListLLM(responses=mock_responses)
        else:
            # Could integrate with local models like Ollama here
            logger.info("Local LLM integration would be implemented here")
            self.llm = None

    def _setup_parsers(self) -> None:
        """Setup output parsers for structured responses."""
        if not LANGCHAIN_AVAILABLE:
            return

        # Create prompt templates for different analysis tasks
        self.summary_prompt = PromptTemplate(
            input_variables=["title", "content"],
            template="""
            Analyze this article and provide a concise 2-3 sentence summary:

            Title: {title}
            Content: {content}

            Summary:
            """,
        )

        self.sentiment_prompt = PromptTemplate(
            input_variables=["title", "content"],
            template="""
            Analyze the sentiment of this article. Respond with exactly one word:
            positive, negative, neutral, or mixed

            Title: {title}
            Content: {content}

            Sentiment:
            """,
        )

        self.topics_prompt = PromptTemplate(
            input_variables=["title", "content"],
            template="""
            Identify the main topics/categories for this article.
            Provide up to 5 topics as comma-separated values.

            Title: {title}
            Content: {content}

            Topics:
            """,
        )

    async def analyze_article(self, article: NewsArticle) -> ContentAnalysis:
        """
        Perform comprehensive AI analysis of a news article.

        Args:
            article: NewsArticle to analyze

        Returns:
            ContentAnalysis with detailed insights
        """
        try:
            logger.info(f"Starting AI analysis for article: {article.title[:50]}...")

            # Extract text content for analysis
            content = article.content or ""
            title = article.title or ""

            # Basic metrics
            word_count = len(content.split()) if content else 0

            if not LANGCHAIN_AVAILABLE or not self.llm:
                return self._fallback_analysis(title, content, word_count)

            # LangChain-powered analysis
            analysis_data = await self._run_llm_analysis(title, content)

            # Combine with rule-based metrics
            quality_score = self._calculate_quality_score(title, content, word_count)
            readability = self._assess_readability(content)
            completeness = self._assess_completeness(article)

            return ContentAnalysis(
                summary=analysis_data.get("summary", "No summary available"),
                sentiment=analysis_data.get("sentiment", "neutral"),
                confidence=0.85,  # Simulated confidence for demo
                quality_score=quality_score,
                readability=readability,
                completeness=completeness,
                topics=analysis_data.get("topics", []),
                entities=analysis_data.get("entities", []),
                language=self._detect_language(content),
                word_count=word_count,
            )

        except Exception as e:
            logger.error(f"Content analysis failed: {e}")
            return self._fallback_analysis(title, content, word_count)

    async def _run_llm_analysis(self, title: str, content: str) -> dict[str, Any]:
        """Run LangChain-powered LLM analysis."""
        try:
            # Truncate content for efficiency
            content_sample = content[:2000] if content else ""

            # Get summary
            summary_chain = self.summary_prompt | self.llm
            summary = await summary_chain.ainvoke(
                {"title": title, "content": content_sample}
            )

            # Get sentiment
            sentiment_chain = self.sentiment_prompt | self.llm
            sentiment = await sentiment_chain.ainvoke(
                {"title": title, "content": content_sample}
            )

            # Get topics
            topics_chain = self.topics_prompt | self.llm
            topics_str = await topics_chain.ainvoke(
                {"title": title, "content": content_sample}
            )
            topics = [t.strip() for t in topics_str.split(",") if t.strip()]

            # Entity extraction (simplified for demo)
            entities = self._extract_entities_basic(content_sample)

            return {
                "summary": summary.strip(),
                "sentiment": sentiment.strip().lower(),
                "topics": topics[:5],  # Limit to 5 topics
                "entities": entities[:10],  # Limit to 10 entities
            }

        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return {}

    def _fallback_analysis(
        self, title: str, content: str, word_count: int
    ) -> ContentAnalysis:
        """Fallback analysis when LangChain is not available."""
        return ContentAnalysis(
            summary=self._generate_simple_summary(title, content),
            sentiment=self._basic_sentiment_analysis(content),
            confidence=0.6,
            quality_score=self._calculate_quality_score(title, content, word_count),
            readability=self._assess_readability(content),
            completeness=0.8,  # Default completeness
            topics=self._extract_topics_basic(title + " " + content),
            entities=self._extract_entities_basic(content),
            language=self._detect_language(content),
            word_count=word_count,
        )

    def _calculate_quality_score(
        self, title: str, content: str, word_count: int
    ) -> float:
        """Calculate content quality score based on multiple factors."""
        score = 5.0  # Base score

        # Title quality
        if title and len(title.strip()) > 10:
            score += 1.0
        if title and not title.isupper():  # Not all caps
            score += 0.5

        # Content length and quality
        if word_count > 100:
            score += 1.0
        if word_count > 500:
            score += 1.0
        if word_count > 1000:
            score += 0.5

        # Content structure indicators
        if content:
            sentences = len([s for s in content.split(".") if s.strip()])
            if sentences > 5:
                score += 0.5
            if "?" in content or "!" in content:  # Engagement indicators
                score += 0.3
            if any(
                word in content.lower()
                for word in ["according to", "research", "study", "data"]
            ):
                score += 0.7  # Authority indicators

        return min(score, 10.0)

    def _assess_readability(self, content: str) -> str:
        """Simple readability assessment."""
        if not content:
            return "unknown"

        words = content.split()
        sentences = [s for s in content.split(".") if s.strip()]

        if not sentences:
            return "basic"

        avg_words_per_sentence = len(words) / len(sentences)

        if avg_words_per_sentence < 15:
            return "basic"
        elif avg_words_per_sentence < 25:
            return "intermediate"
        else:
            return "advanced"

    def _assess_completeness(self, article: NewsArticle) -> float:
        """Assess article completeness based on available fields."""
        completeness = 0.0
        total_fields = 6

        if article.title:
            completeness += 1
        if article.content and len(article.content) > 100:
            completeness += 2  # Content is most important
        if article.author:
            completeness += 1
        if article.published_at:
            completeness += 1
        if article.description:
            completeness += 0.5
        if article.image:
            completeness += 0.5

        return min(completeness / total_fields, 1.0)

    def _detect_language(self, content: str) -> str:
        """Simple language detection (could be enhanced with langdetect library)."""
        if not content:
            return "unknown"

        # Very basic heuristic - in production would use proper language detection
        english_indicators = ["the", "and", "or", "but", "in", "on", "at", "to", "for"]
        content_lower = content.lower()

        english_count = sum(1 for word in english_indicators if word in content_lower)

        return "en" if english_count >= 2 else "unknown"

    def _basic_sentiment_analysis(self, content: str) -> str:
        """Basic rule-based sentiment analysis."""
        if not content:
            return "neutral"

        content_lower = content.lower()

        positive_words = [
            "good",
            "great",
            "excellent",
            "amazing",
            "breakthrough",
            "success",
            "achievement",
        ]
        negative_words = [
            "bad",
            "terrible",
            "crisis",
            "problem",
            "issue",
            "concern",
            "failure",
        ]

        positive_score = sum(1 for word in positive_words if word in content_lower)
        negative_score = sum(1 for word in negative_words if word in content_lower)

        if positive_score > negative_score + 1:
            return "positive"
        elif negative_score > positive_score + 1:
            return "negative"
        else:
            return "neutral"

    def _extract_topics_basic(self, text: str) -> list[str]:
        """Basic topic extraction using keyword matching."""
        if not text:
            return []

        text_lower = text.lower()

        topic_keywords = {
            "technology": [
                "tech",
                "digital",
                "software",
                "computer",
                "ai",
                "artificial intelligence",
            ],
            "business": [
                "business",
                "company",
                "market",
                "economy",
                "finance",
                "startup",
            ],
            "health": [
                "health",
                "medical",
                "hospital",
                "doctor",
                "medicine",
                "treatment",
            ],
            "politics": [
                "government",
                "political",
                "policy",
                "election",
                "president",
                "minister",
            ],
            "science": [
                "research",
                "study",
                "scientist",
                "discovery",
                "experiment",
                "analysis",
            ],
            "sports": ["sport", "game", "team", "player", "championship", "tournament"],
        }

        detected_topics = []
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                detected_topics.append(topic)

        return detected_topics[:3]  # Limit to 3 topics

    def _extract_entities_basic(self, text: str) -> list[str]:
        """Basic entity extraction using pattern matching."""
        if not text:
            return []

        entities = []

        # Find capitalized words/phrases (potential entities)
        words = text.split()
        current_entity = []

        for word in words:
            clean_word = re.sub(r"[^\w]", "", word)
            if clean_word and clean_word[0].isupper() and len(clean_word) > 2:
                current_entity.append(clean_word)
            else:
                if current_entity:
                    entity = " ".join(current_entity)
                    if len(entity) > 3 and entity not in entities:
                        entities.append(entity)
                current_entity = []

        # Add final entity if exists
        if current_entity:
            entity = " ".join(current_entity)
            if len(entity) > 3 and entity not in entities:
                entities.append(entity)

        return entities[:10]  # Limit to 10 entities

    def _generate_simple_summary(self, title: str, content: str) -> str:
        """Generate a simple extractive summary."""
        if not content:
            return title or "No content available for summary."

        # Take first 2 sentences as summary
        sentences = [s.strip() for s in content.split(".") if s.strip()]

        if len(sentences) >= 2:
            return ". ".join(sentences[:2]) + "."
        elif sentences:
            return sentences[0] + "."
        else:
            return title or "No summary available."


# Factory function for easy integration
def create_content_analyzer(use_mock_llm: bool = True) -> AdvancedContentAnalyzer:
    """
    Create a content analyzer instance.

    Args:
        use_mock_llm: Whether to use mock LLM for demonstration

    Returns:
        Configured AdvancedContentAnalyzer instance
    """
    return AdvancedContentAnalyzer(use_mock_llm=use_mock_llm)
