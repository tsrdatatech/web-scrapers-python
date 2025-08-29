"""
Database package initialization.
Provides unified access to database components.
"""

from .cassandra_manager import CassandraManager, CassandraConfig, create_cassandra_manager

__all__ = [
    'CassandraManager',
    'CassandraConfig', 
    'create_cassandra_manager'
]
