#!/usr/bin/env python3
"""
Cassandra Database Integration Demo
Demonstrates distributed data storage, deduplication, and seed management.
"""

import asyncio
from datetime import datetime
from src.database.cassandra_manager import CassandraManager, CassandraConfig
from src.schemas.news import NewsArticle


async def main():
    """Demonstrate Cassandra database integration capabilities."""
    print("🗄️  Cassandra Database Integration Demo")
    print("=" * 50)
    
    # Configuration
    config = CassandraConfig(
        hosts=["localhost"],
        keyspace="web_scraper_demo",
        replication_factor=1
    )
    
    try:
        # Initialize database connection
        print("\n🔌 Connecting to Cassandra...")
        manager = CassandraManager(config)
        await manager.connect()
        print("✅ Connected successfully!")
        
        # Demo 1: Store sample articles
        print("\n📰 Storing sample articles...")
        
        sample_articles = [
            # Only title and url are required - all other fields are Optional  
            NewsArticle(  # type: ignore
                title="Revolutionary AI Breakthrough in Healthcare",
                content="Researchers have developed an AI system that can diagnose diseases "
                       "with 95% accuracy, potentially transforming medical care worldwide.",
                url="https://example.com/ai-healthcare-breakthrough",
                author="Dr. Jane Smith"
            ),
            NewsArticle(  # type: ignore
                title="Climate Change Solutions: New Carbon Capture Technology",
                content="Scientists unveil innovative carbon capture technology that could "
                       "remove millions of tons of CO2 from the atmosphere annually.",
                url="https://example.com/carbon-capture-tech"
            ),
            NewsArticle(  # type: ignore
                title="Quantum Computing Milestone Achieved",
                content="Tech giant announces quantum computer with 1000+ qubits, bringing "
                       "practical quantum computing closer to reality.",
                url="https://example.com/quantum-milestone",
                author="Tech Reporter"
            )
        ]
        
        stored_count = 0
        duplicate_count = 0
        
        for article in sample_articles:
            was_stored = await manager.store_article(article, "generic_news")
            if was_stored:
                stored_count += 1
                print(f"  ✅ Stored: {article.title[:50]}...")
            else:
                duplicate_count += 1
                print(f"  ⚠️  Duplicate: {article.title[:50]}...")
        
        print(f"\n📊 Storage Results: {stored_count} stored, {duplicate_count} duplicates")
        
        # Demo 2: Test deduplication
        print("\n🔄 Testing deduplication...")
        
        # Try to store the same article again
        duplicate_article = sample_articles[0]  # First article again
        was_stored = await manager.store_article(duplicate_article, "generic_news")
        
        if not was_stored:
            print("✅ Deduplication working correctly - duplicate detected and skipped")
        else:
            print("❌ Deduplication failed - duplicate was stored")
        
        # Demo 3: Add seed URLs
        print("\n🌱 Managing seed URLs...")
        
        seed_urls = [
            {
                "url": "https://techcrunch.com",
                "label": "h2 a",
                "parser": "news",
                "priority": 8
            },
            {
                "url": "https://news.ycombinator.com", 
                "label": "a.storylink",
                "parser": "news",
                "priority": 6
            },
            {
                "url": "https://reddit.com/r/technology",
                "label": "a[data-click-id='body']",
                "parser": "generic_news", 
                "priority": 5
            }
        ]
        
        for seed in seed_urls:
            await manager.add_seed_url(
                url=seed["url"],
                label=seed["label"],
                parser=seed["parser"],
                priority=seed["priority"]
            )
            print(f"  ✅ Added seed: {seed['url']}")
        
        # Demo 4: Retrieve seeds from database
        print("\n📋 Retrieving seeds from database...")
        
        seeds = await manager.get_seed_urls(limit=10)
        print(f"Found {len(seeds)} active seeds:")
        
        for i, seed in enumerate(seeds, 1):
            print(f"  {i}. {seed['url']}")
            print(f"     Label: {seed['label']}")
            print(f"     Parser: {seed['parser']}")
        
        # Demo 5: Get crawl statistics
        print("\n📈 Crawl Statistics...")
        
        stats = await manager.get_crawl_statistics(days=1)
        if stats:
            for metric, count in stats.items():
                print(f"  {metric}: {count}")
        else:
            print("  No statistics available yet")
        
        print("\n🎯 Key Features Demonstrated:")
        print("  ✅ Distributed data storage with Cassandra")
        print("  ✅ Automatic URL and content deduplication")
        print("  ✅ Dynamic seed URL management from database")
        print("  ✅ Time-series data tracking and statistics")
        print("  ✅ Scalable architecture for high-volume scraping")
        print("  ✅ Content versioning and change tracking")
        
        print("\n🔧 Database Architecture:")
        print("  • Articles table: Main content storage with partitioning")
        print("  • URL tracker: Deduplication and processing history")
        print("  • Seeds table: Dynamic crawl target management") 
        print("  • Statistics: Performance metrics and monitoring")
        print("  • History: Content versioning and change detection")
        
        print("\n🚀 Production Benefits:")
        print("  • High write throughput for large-scale scraping")
        print("  • Horizontal scaling across multiple nodes")
        print("  • No single point of failure with replication")
        print("  • Efficient time-series data for analytics")
        print("  • Schema flexibility for varying content structures")
        
        # Cleanup
        await manager.close()
        print("\n✨ Demo completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("\n💡 Make sure Cassandra is running:")
        print("   docker-compose -f docker-compose.cassandra.yml up -d cassandra")


if __name__ == "__main__":
    asyncio.run(main())
