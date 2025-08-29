"""
Cassandra database integration for web scraper.
Provides data persistence, deduplication, and seed management.
"""

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from cassandra.auth import PlainTextAuthProvider
    from cassandra.cluster import Cluster
    CASSANDRA_AVAILABLE = True
except ImportError:
    # Cassandra driver not available - create dummy classes for testing
    CASSANDRA_AVAILABLE = False
    
    class PlainTextAuthProvider:
        def __init__(self, *args, **kwargs):
            pass
    
    class Cluster:
        def __init__(self, *args, **kwargs):
            pass
        
        def connect(self):
            raise RuntimeError("Cassandra driver not installed")

from src.core.logger import logger
from src.schemas.news import NewsArticle


@dataclass
class CassandraConfig:
    """Cassandra connection configuration."""

    hosts: List[str] = None
    port: int = 9042
    keyspace: str = "web_scraper"
    username: Optional[str] = None
    password: Optional[str] = None
    replication_factor: int = 1

    def __post_init__(self) -> None:
        if self.hosts is None:
            self.hosts = ["127.0.0.1"]


class CassandraManager:
    """
    Manages Cassandra operations for web scraping data.

    Features:
    - Article storage with time-series partitioning
    - URL deduplication tracking
    - Dynamic seed management
    - Crawl statistics and metrics
    - Content versioning support
    """

    def __init__(self, config: CassandraConfig):
        self.config = config
        self.cluster = None
        self.session = None
        self._prepared_statements: Dict[str, Any] = {}

    async def connect(self) -> None:
        """Establish connection to Cassandra cluster."""
        try:
            # Setup authentication if provided
            auth_provider = None
            if self.config.username and self.config.password:
                auth_provider = PlainTextAuthProvider(
                    username=self.config.username, password=self.config.password
                )

            # Create cluster connection
            self.cluster = Cluster(
                contact_points=self.config.hosts,
                port=self.config.port,
                auth_provider=auth_provider,
            )

            self.session = self.cluster.connect()

            # Create keyspace and tables
            await self._create_keyspace()
            await self._create_tables()
            await self._prepare_statements()

            logger.info(
                "Connected to Cassandra cluster",
                hosts=self.config.hosts,
                keyspace=self.config.keyspace,
            )

        except Exception as e:
            logger.error("Failed to connect to Cassandra", error=str(e))
            raise

    async def _create_keyspace(self) -> None:
        """Create keyspace if it doesn't exist."""
        create_keyspace = f"""
        CREATE KEYSPACE IF NOT EXISTS {self.config.keyspace}
        WITH replication = {{
            'class': 'SimpleStrategy',
            'replication_factor': {self.config.replication_factor}
        }}
        """
        self.session.execute(create_keyspace)
        self.session.set_keyspace(self.config.keyspace)

    async def _create_tables(self) -> None:
        """Create all required tables."""

        # Articles table - main content storage
        create_articles = """
        CREATE TABLE IF NOT EXISTS articles (
            article_id UUID PRIMARY KEY,
            url TEXT,
            url_hash TEXT,
            title TEXT,
            content TEXT,
            author TEXT,
            published_date TIMESTAMP,
            scraped_at TIMESTAMP,
            source_domain TEXT,
            parser_used TEXT,
            content_hash TEXT,
            ai_analysis TEXT,  -- JSON string of AI analysis
            metadata MAP<TEXT, TEXT>,
            version INT,
            status TEXT  -- 'active', 'duplicate', 'error'
        )
        """

        # URL deduplication table
        create_url_tracker = """
        CREATE TABLE IF NOT EXISTS url_tracker (
            url_hash TEXT PRIMARY KEY,
            original_url TEXT,
            first_seen TIMESTAMP,
            last_seen TIMESTAMP,
            scrape_count INT,
            last_article_id UUID,
            status TEXT  -- 'pending', 'processed', 'failed', 'skipped'
        )
        """

        # Seeds management table
        create_seeds = """
        CREATE TABLE IF NOT EXISTS seeds (
            seed_id UUID PRIMARY KEY,
            url TEXT,
            label TEXT,
            parser TEXT,
            priority INT,
            added_at TIMESTAMP,
            last_used TIMESTAMP,
            success_count INT,
            failure_count INT,
            status TEXT,  -- 'active', 'inactive', 'exhausted'
            metadata MAP<TEXT, TEXT>
        )
        """

        # Crawl statistics table
        create_stats = """
        CREATE TABLE IF NOT EXISTS crawl_stats (
            date DATE,
            hour INT,
            metric_type TEXT,  -- 'articles_scraped', 'urls_processed', 'errors'
            count COUNTER,
            PRIMARY KEY ((date, hour), metric_type)
        )
        """

        # Content history for versioning
        create_history = """
        CREATE TABLE IF NOT EXISTS content_history (
            url_hash TEXT,
            scraped_at TIMESTAMP,
            article_id UUID,
            content_hash TEXT,
            change_type TEXT,  -- 'new', 'updated', 'unchanged'
            PRIMARY KEY (url_hash, scraped_at)
        ) WITH CLUSTERING ORDER BY (scraped_at DESC)
        """

        tables = [
            create_articles,
            create_url_tracker,
            create_seeds,
            create_stats,
            create_history,
        ]

        for table_cql in tables:
            self.session.execute(table_cql)

        logger.info("Created Cassandra tables successfully")

    async def _prepare_statements(self) -> None:
        """Prepare frequently used statements for better performance."""
        statements = {
            "insert_article": """
                INSERT INTO articles (
                    article_id, url, url_hash, title, content, author,
                    published_date, scraped_at, source_domain, parser_used,
                    content_hash, ai_analysis, metadata, version, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            "check_url_exists": """
                SELECT url_hash, last_article_id, status
                FROM url_tracker WHERE url_hash = ?
            """,
            "update_url_tracker": """
                UPDATE url_tracker SET
                    last_seen = ?, scrape_count = scrape_count + 1,
                    last_article_id = ?, status = ?
                WHERE url_hash = ?
            """,
            "insert_url_tracker": """
                INSERT INTO url_tracker (
                    url_hash, original_url, first_seen, last_seen,
                    scrape_count, last_article_id, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            "get_active_seeds": """
                SELECT seed_id, url, label, parser, priority
                FROM seeds WHERE status = 'active'
                ORDER BY priority DESC
            """,
            "update_crawl_stats": """
                UPDATE crawl_stats SET count = count + 1
                WHERE date = ? AND hour = ? AND metric_type = ?
            """,
        }

        for name, cql in statements.items():
            self._prepared_statements[name] = self.session.prepare(cql)

    async def store_article(self, article: NewsArticle, parser_name: str) -> bool:
        """
        Store scraped article with deduplication check.

        Returns True if article was stored, False if duplicate.
        """
        try:
            url_hash = self._hash_url(article.url)
            content_hash = self._hash_content(article.content)

            # Check for duplicates
            if await self._is_duplicate(url_hash, content_hash):
                await self._update_duplicate_tracking(url_hash)
                return False

            # Generate article ID
            article_id = uuid.uuid4()
            now = datetime.utcnow()

            # Prepare AI analysis JSON
            ai_analysis_json = None
            if article.ai_analysis:
                ai_analysis_json = json.dumps(article.ai_analysis)

            # Store article
            self.session.execute(
                self._prepared_statements["insert_article"],
                [
                    article_id,
                    str(article.url),
                    url_hash,
                    article.title,
                    article.content,
                    article.author,
                    article.published_at,
                    now,
                    self._extract_domain(str(article.url)),
                    parser_name,
                    content_hash,
                    ai_analysis_json,
                    {},  # metadata
                    1,  # version
                    "active",
                ],
            )

            # Update URL tracking
            await self._update_url_tracking(url_hash, str(article.url), article_id)

            # Update statistics
            await self._update_statistics("articles_scraped")

            # Store content history
            await self._store_content_history(url_hash, article_id, content_hash, "new")

            logger.info(
                "Stored article in Cassandra",
                article_id=str(article_id),
                url=str(article.url),
                title=article.title[:50],
            )

            return True

        except Exception as e:
            logger.error("Failed to store article", error=str(e), url=str(article.url))
            await self._update_statistics("errors")
            raise

    async def _is_duplicate(self, url_hash: str, content_hash: str) -> bool:
        """Check if URL or content already exists."""
        # Check URL tracking
        result = self.session.execute(
            self._prepared_statements["check_url_exists"], [url_hash]
        )

        if result.one():
            # URL already processed
            return True

        # Could add content hash checking for near-duplicate detection
        return False

    async def _update_url_tracking(
        self, url_hash: str, url: str, article_id: uuid.UUID
    ) -> None:
        """Update URL tracking information."""
        now = datetime.utcnow()

        # Try to update existing record
        existing = self.session.execute(
            self._prepared_statements["check_url_exists"], [url_hash]
        ).one()

        if existing:
            self.session.execute(
                self._prepared_statements["update_url_tracker"],
                [now, article_id, "processed", url_hash],
            )
        else:
            self.session.execute(
                self._prepared_statements["insert_url_tracker"],
                [url_hash, url, now, now, 1, article_id, "processed"],
            )

    async def get_seed_urls(self, limit: int = 100) -> List[Dict[str, str]]:
        """Retrieve active seed URLs for crawling."""
        try:
            result = self.session.execute(self._prepared_statements["get_active_seeds"])

            seeds = []
            for row in result:
                seeds.append(
                    {
                        "url": row.url,
                        "label": row.label or "",
                        "parser": row.parser or "auto",
                    }
                )

                if len(seeds) >= limit:
                    break

            logger.info(f"Retrieved {len(seeds)} seed URLs from Cassandra")
            return seeds

        except Exception as e:
            logger.error("Failed to retrieve seeds", error=str(e))
            return []

    async def add_seed_url(
        self,
        url: str,
        label: Optional[str] = None,
        parser: Optional[str] = None,
        priority: int = 1,
    ) -> None:
        """Add new seed URL to the database."""
        try:
            seed_id = uuid.uuid4()
            now = datetime.utcnow()

            insert_seed = """
                INSERT INTO seeds (
                    seed_id, url, label, parser, priority, added_at,
                    last_used, success_count, failure_count, status, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            self.session.execute(
                insert_seed,
                [seed_id, url, label, parser, priority, now, None, 0, 0, "active", {}],
            )

            logger.info("Added seed URL", url=url, seed_id=str(seed_id))

        except Exception as e:
            logger.error("Failed to add seed URL", error=str(e), url=url)
            raise

    def _hash_url(self, url: str) -> str:
        """Generate consistent hash for URL."""
        return hashlib.sha256(url.encode()).hexdigest()[:16]

    def _hash_content(self, content: str) -> str:
        """Generate hash for content deduplication."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        from urllib.parse import urlparse

        return urlparse(url).netloc

    async def _update_statistics(self, metric_type: str) -> None:
        """Update crawl statistics."""
        try:
            now = datetime.utcnow()
            date = now.date()
            hour = now.hour

            self.session.execute(
                self._prepared_statements["update_crawl_stats"],
                [date, hour, metric_type],
            )
        except Exception as e:
            logger.warning("Failed to update statistics", error=str(e))

    async def _store_content_history(
        self, url_hash: str, article_id: uuid.UUID, content_hash: str, change_type: str
    ) -> None:
        """Store content version history."""
        try:
            insert_history = """
                INSERT INTO content_history (
                    url_hash, scraped_at, article_id, content_hash, change_type
                ) VALUES (?, ?, ?, ?, ?)
            """

            self.session.execute(
                insert_history,
                [url_hash, datetime.utcnow(), article_id, content_hash, change_type],
            )
        except Exception as e:
            logger.warning("Failed to store content history", error=str(e))

    async def _update_duplicate_tracking(self, url_hash: str) -> None:
        """Update tracking for duplicate URLs."""
        try:
            now = datetime.utcnow()
            self.session.execute(
                self._prepared_statements["update_url_tracker"],
                [now, None, "duplicate", url_hash],
            )
            await self._update_statistics("duplicates_skipped")
        except Exception as e:
            logger.warning("Failed to update duplicate tracking", error=str(e))

    async def get_crawl_statistics(self, days: int = 7) -> Dict[str, int]:
        """Get crawl statistics for the last N days."""
        try:
            from datetime import date, timedelta

            stats = {}
            end_date = date.today()
            start_date = end_date - timedelta(days=days)

            query = """
                SELECT metric_type, SUM(count) as total
                FROM crawl_stats
                WHERE date >= ? AND date <= ?
                GROUP BY metric_type
            """

            result = self.session.execute(query, [start_date, end_date])

            for row in result:
                stats[row.metric_type] = int(row.total)

            return stats

        except Exception as e:
            logger.error("Failed to get statistics", error=str(e))
            return {}

    async def close(self) -> None:
        """Close Cassandra connection."""
        if self.cluster:
            self.cluster.shutdown()
            logger.info("Closed Cassandra connection")


# Factory function for easy initialization
async def create_cassandra_manager(
    config: Optional[CassandraConfig] = None,
) -> CassandraManager:
    """Create and connect to Cassandra manager."""
    if config is None:
        config = CassandraConfig()

    manager = CassandraManager(config)
    await manager.connect()
    return manager
