"""
Enhanced parser manager with Cassandra integration.
Provides persistent storage, deduplication, and seed management.
"""


from src.core.logger import logger
from src.core.parser_manager import ParserManager as BaseParserManager

try:
    from src.database.cassandra_manager import (
        CASSANDRA_AVAILABLE,
        CassandraConfig,
        CassandraManager,
    )
except ImportError:
    CASSANDRA_AVAILABLE = False

    # Create dummy classes for when Cassandra is not available
    class CassandraConfig:
        pass

    class CassandraManager:
        pass


from src.schemas.news import NewsArticle


class CassandraParserManager(BaseParserManager):
    """
    Enhanced parser manager with Cassandra database integration.

    Features:
    - Automatic deduplication of scraped content
    - Persistent storage of articles with AI analysis
    - Dynamic seed URL management from database
    - Crawl statistics and performance tracking
    """

    def __init__(self, registry, cassandra_config: CassandraConfig | None = None):
        super().__init__(registry)
        self.cassandra_config = cassandra_config or CassandraConfig()
        self.db_manager: CassandraManager | None = None
        self._stats = {"articles_stored": 0, "duplicates_skipped": 0, "errors": 0}

    async def initialize(self) -> None:
        """Initialize Cassandra connection."""
        try:
            from src.database.cassandra_manager import create_cassandra_manager

            self.db_manager = await create_cassandra_manager(self.cassandra_config)
            logger.info("Cassandra integration initialized successfully")
        except Exception as e:
            logger.warning(
                "Failed to initialize Cassandra, running without database", error=str(e)
            )
            self.db_manager = None

    async def store_article(self, article: NewsArticle, parser_name: str) -> bool:
        """
        Store article with automatic deduplication.

        Returns:
            True if article was stored (new content)
            False if article was skipped (duplicate)
        """
        if not self.db_manager:
            logger.warning("No database connection, skipping storage")
            return True

        try:
            was_stored = await self.db_manager.store_article(article, parser_name)

            if was_stored:
                self._stats["articles_stored"] += 1
                logger.info(
                    "Article stored successfully",
                    title=article.title[:50],
                    url=str(article.url),
                )
            else:
                self._stats["duplicates_skipped"] += 1
                logger.info("Duplicate article skipped", url=str(article.url))

            return was_stored

        except Exception as e:
            self._stats["errors"] += 1
            logger.error("Failed to store article", error=str(e), url=str(article.url))
            # Don't re-raise - continue scraping even if storage fails
            return False

    async def get_seed_urls(self, limit: int = 100) -> list[dict[str, str]]:
        """
        Get seed URLs from database instead of file.
        Falls back to file-based seeds if database unavailable.
        """
        if not self.db_manager:
            logger.info("No database connection, using file-based seeds")
            return await self._get_file_based_seeds()

        try:
            seeds = await self.db_manager.get_seed_urls(limit)

            if not seeds:
                logger.warning("No seeds found in database, falling back to file")
                return await self._get_file_based_seeds()

            logger.info(f"Retrieved {len(seeds)} seeds from Cassandra")
            return seeds

        except Exception as e:
            logger.error("Failed to get seeds from database", error=str(e))
            return await self._get_file_based_seeds()

    async def add_seed_url(
        self,
        url: str,
        label: str | None = None,
        parser: str | None = None,
        priority: int = 1,
    ) -> None:
        """Add new seed URL to database."""
        if not self.db_manager:
            logger.warning("No database connection, cannot add seed")
            return

        try:
            await self.db_manager.add_seed_url(url, label, parser, priority)
            logger.info("Added seed URL to database", url=url)
        except Exception as e:
            logger.error("Failed to add seed URL", error=str(e), url=url)

    async def get_crawl_statistics(self) -> dict[str, int]:
        """Get comprehensive crawl statistics."""
        stats = self._stats.copy()

        if self.db_manager:
            try:
                db_stats = await self.db_manager.get_crawl_statistics()
                stats.update(db_stats)
            except Exception as e:
                logger.error("Failed to get database statistics", error=str(e))

        return stats

    async def _get_file_based_seeds(self) -> list[dict[str, str]]:
        """Fallback to file-based seed loading."""
        try:
            from src.core.seeds import parse_seeds_file

            # Use default seeds file
            seeds = await parse_seeds_file("seeds.txt")
            return seeds
        except Exception as e:
            logger.error("Failed to load file-based seeds", error=str(e))
            return []

    async def cleanup(self) -> None:
        """Clean up database connections."""
        if self.db_manager:
            await self.db_manager.close()

        # Log final statistics
        stats = await self.get_crawl_statistics()
        logger.info("Final crawl statistics", **stats)


# Factory function for creating enhanced parser manager
async def create_cassandra_parser_manager(
    registry, cassandra_config: CassandraConfig | None = None
):
    """Create parser manager with Cassandra integration."""
    manager = CassandraParserManager(registry, cassandra_config)
    await manager.initialize()
    return manager
