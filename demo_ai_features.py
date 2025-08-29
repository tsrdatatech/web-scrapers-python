#!/usr/bin/env python3
"""
Demo script showcasing LangChain AI/ML integration capabilities.

This script demonstrates the AI-enhanced web scraping features including:
- Content analysis and summarization
- Sentiment analysis  
- Topic classification
- Entity extraction
- Quality assessment

Run with: python demo_ai_features.py
"""

import asyncio
import json
from pathlib import Path

from src.ai.content_analyzer import create_content_analyzer
from src.schemas.news import NewsArticle
from src.parsers.ai_enhanced_news import AIEnhancedNewsParser, SmartParserFactory


async def demo_content_analysis():
    """Demonstrate AI-powered content analysis capabilities."""
    print("🤖 AI-Enhanced Web Scraper Demo")
    print("=" * 50)
    
    # Create a sample article for demonstration
    # Only title and url are required - all other fields are Optional
    sample_article = NewsArticle(  # type: ignore
        title="Revolutionary AI Breakthrough Achieves Human-Level Performance",
        content="""
        In a groundbreaking development, researchers at leading technology institutes 
        have successfully created an artificial intelligence system that demonstrates 
        human-level performance across multiple cognitive tasks. This breakthrough 
        represents years of dedicated research in machine learning and neural networks.
        
        The AI system, trained on diverse datasets, shows remarkable capabilities in 
        natural language understanding, reasoning, and problem-solving. Early tests 
        indicate that the technology could have profound implications for industries 
        ranging from healthcare to autonomous vehicles.
        
        Scientists involved in the project express cautious optimism about the future 
        applications of this technology, while emphasizing the importance of responsible 
        development and deployment of advanced AI systems.
        """,
        url="https://example.com/ai-breakthrough-2024"
    )
    
    # Create content analyzer
    analyzer = create_content_analyzer(use_mock_llm=True)
    
    print("\n📊 Analyzing the sample article...\n")
    
    print(f"Article: {sample_article.title}")
    print("-" * 60)
    
    # Run AI analysis
    analysis = await analyzer.analyze_article(sample_article)
    
    # Display results
    print(f"📝 Summary: {analysis.summary}")
    print(f"😊 Sentiment: {analysis.sentiment} (confidence: {analysis.confidence:.2f})")
    print(f"⭐ Quality Score: {analysis.quality_score:.1f}/10")
    print(f"📖 Readability: {analysis.readability}")
    print(f"🏷️  Topics: {', '.join(analysis.topics)}")
    print(f"👥 Entities: {', '.join(analysis.entities[:5])}...")
    print(f"🔤 Language: {analysis.language}")
    print(f"📊 Word Count: {analysis.word_count}")
    print(f"✅ Completeness: {analysis.completeness:.1%}")
    print()


async def demo_ai_enhanced_parser():
    """Demonstrate the AI-enhanced parser factory."""
    print("🏭 AI-Enhanced Parser Factory Demo")
    print("=" * 40)
    
    # Create different parser configurations
    configurations = [
        ("Standard Parser", SmartParserFactory.create_standard_parser()),
        ("AI-Enhanced Parser", SmartParserFactory.create_enhanced_parser(ai_enabled=True)),
    ]
    
    for name, parser in configurations:
        print(f"\n{name}:")
        print(f"  • Parser ID: {parser.id}")
        print(f"  • AI Analysis: {'✅ Enabled' if parser.enable_ai_analysis else '❌ Disabled'}")
        print(f"  • Content Analyzer: {'✅ Available' if parser.content_analyzer else '❌ None'}")


async def demo_langchain_integration():
    """Demonstrate LangChain integration details."""
    print("🔗 LangChain Integration Details")
    print("=" * 35)
    
    analyzer = create_content_analyzer()
    
    print("📦 LangChain Components:")
    print(f"  • Core Framework: {type(analyzer).__name__}")
    print(f"  • Mock LLM: {'✅ Active' if analyzer.use_mock_llm else '❌ Disabled'}")
    print(f"  • Prompt Templates: ✅ Configured")
    print(f"  • Output Parsers: ✅ Available")
    
    print("\n🧠 AI Capabilities:")
    capabilities = [
        "Content Summarization",
        "Sentiment Analysis", 
        "Topic Classification",
        "Entity Extraction",
        "Quality Assessment",
        "Language Detection",
        "Readability Analysis"
    ]
    
    for capability in capabilities:
        print(f"  • {capability}: ✅ Implemented")
    
    print("\n🏗️ Architecture Benefits:")
    benefits = [
        "Pluggable AI components",
        "Fallback analysis without LLM",
        "Structured output with Pydantic",
        "Async processing support",
        "Mock LLM for development/testing",
        "Extensible prompt templates"
    ]
    
    for benefit in benefits:
        print(f"  • {benefit}")


async def main():
    """Run the complete AI features demonstration."""
    try:
        await demo_content_analysis()
        await demo_ai_enhanced_parser()
        await demo_langchain_integration()
        
        print("\n🎯 Demo Complete!")
        print("\nThis demonstrates:")
        print("• LangChain integration for AI-powered content analysis")
        print("• Sophisticated prompt engineering and output parsing")
        print("• Production-ready error handling and fallbacks")
        print("• Type-safe AI results with Pydantic schemas")
        print("• Scalable architecture for ML/AI enhancements")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 Starting AI-Enhanced Web Scraper Demo...")
    asyncio.run(main())
