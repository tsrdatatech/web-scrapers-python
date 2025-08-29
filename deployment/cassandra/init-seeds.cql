# Cassandra initialization script
# Creates keyspace and initial seed data

# Create keyspace
CREATE KEYSPACE IF NOT EXISTS web_scraper
WITH replication = {
    'class': 'SimpleStrategy',
    'replication_factor': 1
};

USE web_scraper;

# Sample seed URLs
INSERT INTO seeds (seed_id, url, label, parser, priority, added_at, success_count, failure_count, status, metadata)
VALUES (uuid(), 'https://example.com/news', 'a.article-link', 'news', 5, toTimestamp(now()), 0, 0, 'active', {});

INSERT INTO seeds (seed_id, url, label, parser, priority, added_at, success_count, failure_count, status, metadata)  
VALUES (uuid(), 'https://techcrunch.com', 'a[data-module="ArticleCard"]', 'news', 8, toTimestamp(now()), 0, 0, 'active', {});

INSERT INTO seeds (seed_id, url, label, parser, priority, added_at, success_count, failure_count, status, metadata)
VALUES (uuid(), 'https://news.ycombinator.com', 'a.storylink', 'news', 6, toTimestamp(now()), 0, 0, 'active', {});

# Sample configuration
INSERT INTO seeds (seed_id, url, label, parser, priority, added_at, success_count, failure_count, status, metadata)
VALUES (uuid(), 'https://reddit.com/r/technology', 'a[data-click-id="body"]', 'generic_news', 4, toTimestamp(now()), 0, 0, 'active', {'source': 'reddit'});
