"""
Parser registry for auto-discovery and management of parsers.
"""

import os
import importlib.util
import sys
from pathlib import Path
from typing import Dict, List, Optional

from .base_parser import BaseParser
from .logger import logger


class ParserRegistry:
    """Registry for managing and discovering parsers."""
    
    def __init__(self) -> None:
        self.parsers: Dict[str, BaseParser] = {}
    
    def register(self, parser: BaseParser) -> None:
        """Register a parser instance."""
        self.parsers[parser.id] = parser
        logger.info(f"Registered parser: {parser.id}")
    
    def get(self, parser_id: str) -> Optional[BaseParser]:
        """Get a parser by ID."""
        return self.parsers.get(parser_id)
    
    def all(self) -> List[BaseParser]:
        """Get all registered parsers."""
        return list(self.parsers.values())
    
    def get_by_domain(self, domain: str) -> List[BaseParser]:
        """Get parsers that can handle a specific domain."""
        return [
            parser for parser in self.parsers.values()
            if domain in parser.domains
        ]


async def create_parser_registry() -> ParserRegistry:
    """
    Create and populate parser registry by auto-discovering parsers.
    
    Returns:
        Populated ParserRegistry instance
    """
    registry = ParserRegistry()
    
    # Get the parsers directory
    current_dir = Path(__file__).parent.parent
    parsers_dir = current_dir / "parsers"
    
    if not parsers_dir.exists():
        logger.warning(f"Parsers directory not found: {parsers_dir}")
        return registry
    
    # Load all Python files in parsers directory
    for parser_file in parsers_dir.glob("*.py"):
        if parser_file.name.startswith("__"):
            continue
            
        try:
            # Dynamic import
            spec = importlib.util.spec_from_file_location(
                f"parsers.{parser_file.stem}", 
                parser_file
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Look for parser classes
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type) and
                        issubclass(attr, BaseParser) and
                        attr is not BaseParser
                    ):
                        # Instantiate and register
                        parser_instance = attr()
                        registry.register(parser_instance)
                        break
                        
        except Exception as e:
            logger.error(f"Failed to load parser from {parser_file}: {e}")
    
    return registry
