"""
Abstract base class for all parsers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from playwright.async_api import Page
from pydantic import BaseModel


class BaseParser(ABC):
    """Abstract base class for all site-specific parsers."""

    id: str = "base"
    schema: Optional[type[BaseModel]] = None  # Pydantic model class
    domains: List[str] = []  # Optional list of domains it handles

    @abstractmethod
    async def can_parse(
        self, url: str, context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Determine if this parser can handle the given URL.

        Args:
            url: The URL to check
            context: Optional context data

        Returns:
            True if this parser can handle the URL
        """
        return False

    @abstractmethod
    async def parse(self, page: Page, context: Dict[str, Any]) -> Optional[BaseModel]:
        """
        Parse the page and extract structured data.

        Args:
            page: Playwright page object
            context: Context containing request, page, logger, etc.

        Returns:
            Validated data model or None if parsing fails
        """
        raise NotImplementedError("parse() method must be implemented")

    def validate_data(self, data: Dict[str, Any]) -> BaseModel:
        """
        Validate raw data against the parser's schema.

        Args:
            data: Raw extracted data

        Returns:
            Validated Pydantic model instance

        Raises:
            ValidationError: If data doesn't match schema
        """
        if not self.schema:
            raise ValueError(f"Parser {self.id} has no schema defined")

        return self.schema(**data)
