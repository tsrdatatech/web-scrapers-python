"""
Tests for Cassandra database integration.
"""

from unittest.mock import Mock, patch

import pytest

from src.database.cassandra_manager import CassandraConfig, CassandraManager
from src.schemas.news import NewsArticle


class TestCassandraManager:
    """Test cases for Cassandra database manager."""

    @pytest.fixture
    def mock_session(self):
        """Create mock Cassandra session."""
        session = Mock()
        session.execute = Mock()
        session.prepare = Mock()
        session.set_keyspace = Mock()
        return session

    @pytest.fixture
    def mock_cluster(self, mock_session):
        """Create mock Cassandra cluster."""
        cluster = Mock()
        cluster.connect.return_value = mock_session
        cluster.shutdown = Mock()
        return cluster

    @pytest.fixture
    def cassandra_config(self):
        """Create test Cassandra configuration."""
        return CassandraConfig(
            hosts=["localhost"], keyspace="test_scraper", replication_factor=1
        )

    @pytest.fixture
    def cassandra_manager(self, cassandra_config):
        """Create Cassandra manager instance."""
        return CassandraManager(cassandra_config)

    @pytest.fixture
    def sample_article(self):
        """Create sample NewsArticle for testing."""
        # Only title and url are required - all other fields are Optional
        return NewsArticle(  # type: ignore
            title="Sample Technology Article",
            content="This is a sample article about technology and innovation. "
            "It contains enough content to test the storage functionality.",
            url="https://example.com/tech-article",
        )

    @pytest.mark.asyncio
    async def test_cassandra_config_defaults(self):
        """Test default configuration values."""
        config = CassandraConfig()

        assert config.hosts == ["127.0.0.1"]
        assert config.port == 9042
        assert config.keyspace == "web_scraper"
        assert config.replication_factor == 1
        assert config.username is None
        assert config.password is None

    @pytest.mark.asyncio
    async def test_cassandra_manager_initialization(
        self, cassandra_manager, cassandra_config
    ):
        """Test manager initialization with configuration."""
        assert cassandra_manager.config == cassandra_config
        assert cassandra_manager.cluster is None
        assert cassandra_manager.session is None

    @pytest.mark.asyncio
    async def test_store_article_success(
        self, cassandra_manager, mock_cluster, mock_session, sample_article
    ):
        """Test successful article storage."""
        # Mock cluster and session
        with patch("src.database.cassandra_manager.Cluster", return_value=mock_cluster):
            cassandra_manager.cluster = mock_cluster
            cassandra_manager.session = mock_session

            # Mock prepared statements
            mock_prepared = Mock()
            cassandra_manager._prepared_statements = {
                "insert_article": mock_prepared,
                "check_url_exists": mock_prepared,
                "insert_url_tracker": mock_prepared,
                "update_crawl_stats": mock_prepared,
            }

            # Mock no existing URL (not duplicate)
            mock_result = Mock()
            mock_result.one.return_value = None
            mock_session.execute.return_value = mock_result

            # Test article storage
            result = await cassandra_manager.store_article(
                sample_article, "generic_news"
            )

            # Verify article was stored (not duplicate)
            assert result is True

            # Verify database calls were made
            assert (
                mock_session.execute.call_count >= 3
            )  # check_url, insert_article, insert_url_tracker

    @pytest.mark.asyncio
    async def test_store_article_duplicate(
        self, cassandra_manager, mock_cluster, mock_session, sample_article
    ):
        """Test duplicate article detection."""
        with patch("src.database.cassandra_manager.Cluster", return_value=mock_cluster):
            cassandra_manager.cluster = mock_cluster
            cassandra_manager.session = mock_session

            # Mock prepared statements
            mock_prepared = Mock()
            cassandra_manager._prepared_statements = {
                "check_url_exists": mock_prepared,
                "update_url_tracker": mock_prepared,
                "update_crawl_stats": mock_prepared,
            }

            # Mock existing URL (duplicate)
            mock_row = Mock()
            mock_row.url_hash = "existing_hash"
            mock_result = Mock()
            mock_result.one.return_value = mock_row
            mock_session.execute.return_value = mock_result

            # Test duplicate detection
            result = await cassandra_manager.store_article(
                sample_article, "generic_news"
            )

            # Verify article was not stored (duplicate)
            assert result is False

    @pytest.mark.asyncio
    async def test_get_seed_urls(self, cassandra_manager, mock_cluster, mock_session):
        """Test retrieving seed URLs from database."""
        with patch("src.database.cassandra_manager.Cluster", return_value=mock_cluster):
            cassandra_manager.cluster = mock_cluster
            cassandra_manager.session = mock_session

            # Mock prepared statements
            mock_prepared = Mock()
            cassandra_manager._prepared_statements = {"get_active_seeds": mock_prepared}

            # Mock seed data
            mock_rows = [
                Mock(
                    url="https://example.com/news",
                    label="a.article-link",
                    parser="news",
                ),
                Mock(url="https://techcrunch.com", label="h2 a", parser="news"),
                Mock(
                    url="https://reddit.com/r/tech",
                    label="a[data-click-id]",
                    parser="generic_news",
                ),
            ]
            mock_session.execute.return_value = mock_rows

            # Test seed retrieval
            seeds = await cassandra_manager.get_seed_urls(limit=10)

            # Verify seeds were retrieved correctly
            assert len(seeds) == 3
            assert seeds[0]["url"] == "https://example.com/news"
            assert seeds[0]["label"] == "a.article-link"
            assert seeds[0]["parser"] == "news"

    @pytest.mark.asyncio
    async def test_add_seed_url(self, cassandra_manager, mock_cluster, mock_session):
        """Test adding new seed URL to database."""
        with patch("src.database.cassandra_manager.Cluster", return_value=mock_cluster):
            cassandra_manager.cluster = mock_cluster
            cassandra_manager.session = mock_session

            # Test adding seed URL
            await cassandra_manager.add_seed_url(
                url="https://new-site.com",
                label="a.news-link",
                parser="news",
                priority=8,
            )

            # Verify database insert was called
            mock_session.execute.assert_called()

    @pytest.mark.asyncio
    async def test_url_hashing_consistency(self, cassandra_manager):
        """Test URL hashing produces consistent results."""
        url = "https://example.com/article"

        hash1 = cassandra_manager._hash_url(url)
        hash2 = cassandra_manager._hash_url(url)

        # Verify hashes are consistent
        assert hash1 == hash2
        assert len(hash1) == 16  # Truncated to 16 characters
        assert isinstance(hash1, str)

    @pytest.mark.asyncio
    async def test_content_hashing(self, cassandra_manager):
        """Test content hashing for deduplication."""
        content1 = "This is sample article content for testing."
        content2 = "This is different article content."

        hash1 = cassandra_manager._hash_content(content1)
        hash2 = cassandra_manager._hash_content(content2)
        hash3 = cassandra_manager._hash_content(content1)  # Same as content1

        # Verify different content produces different hashes
        assert hash1 != hash2
        # Verify same content produces same hash
        assert hash1 == hash3
        assert len(hash1) == 16

    @pytest.mark.asyncio
    async def test_domain_extraction(self, cassandra_manager):
        """Test domain extraction from URLs."""
        test_cases = [
            ("https://example.com/article", "example.com"),
            ("http://news.site.org/tech", "news.site.org"),
            ("https://subdomain.domain.com:8080/path", "subdomain.domain.com:8080"),
        ]

        for url, expected_domain in test_cases:
            domain = cassandra_manager._extract_domain(url)
            assert domain == expected_domain

    @pytest.mark.asyncio
    async def test_get_crawl_statistics(
        self, cassandra_manager, mock_cluster, mock_session
    ):
        """Test crawl statistics retrieval."""
        with patch("src.database.cassandra_manager.Cluster", return_value=mock_cluster):
            cassandra_manager.cluster = mock_cluster
            cassandra_manager.session = mock_session

            # Mock statistics data
            mock_rows = [
                Mock(metric_type="articles_scraped", total=150),
                Mock(metric_type="duplicates_skipped", total=23),
                Mock(metric_type="errors", total=5),
            ]
            mock_session.execute.return_value = mock_rows

            # Test statistics retrieval
            stats = await cassandra_manager.get_crawl_statistics(days=7)

            # Verify statistics format
            assert stats["articles_scraped"] == 150
            assert stats["duplicates_skipped"] == 23
            assert stats["errors"] == 5

    @pytest.mark.asyncio
    async def test_connection_error_handling(self, cassandra_config):
        """Test graceful handling of connection errors."""
        manager = CassandraManager(cassandra_config)

        # Mock connection failure
        with patch(
            "src.database.cassandra_manager.Cluster",
            side_effect=Exception("Connection failed"),
        ):
            with pytest.raises(Exception, match="Connection failed"):
                await manager.connect()

    @pytest.mark.asyncio
    async def test_create_cassandra_manager_factory(self):
        """Test factory function for creating manager."""
        from src.database.cassandra_manager import create_cassandra_manager

        # Mock successful connection
        with patch(
            "src.database.cassandra_manager.CassandraManager.connect"
        ) as mock_connect:
            mock_connect.return_value = None

            # Test factory with default config
            manager = await create_cassandra_manager()

            assert isinstance(manager, CassandraManager)
            assert manager.config.keyspace == "web_scraper"
            mock_connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_connection(self, cassandra_manager, mock_cluster):
        """Test closing Cassandra connection."""
        cassandra_manager.cluster = mock_cluster

        await cassandra_manager.close()

        # Verify cluster shutdown was called
        mock_cluster.shutdown.assert_called_once()
