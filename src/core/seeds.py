"""
Seed file parsing and URL resolution.
"""

import json
import re
from pathlib import Path
from typing import Any

import aiofiles

from .logger import logger


async def resolve_seeds(args: Any) -> list[dict[str, Any]]:
    """
    Resolve seed URLs from command line arguments.

    Args:
        args: Parsed command line arguments

    Returns:
        List of seed dictionaries with url, label, parser keys
    """
    if hasattr(args, "url") and args.url:
        seed = {"url": args.url}
        if hasattr(args, "label") and args.label:
            seed["label"] = args.label
        if hasattr(args, "parser") and args.parser:
            seed["parser"] = args.parser
        return [seed]

    if hasattr(args, "file") and args.file:
        return await parse_seeds_file(args.file)

    raise ValueError("Provide --url or --file argument")


async def parse_seeds_file(file_path: str) -> list[dict[str, Any]]:
    """
    Parse seeds from a file.

    Args:
        file_path: Path to the seeds file

    Returns:
        List of parsed seed dictionaries
    """
    if not Path(file_path).exists():
        raise FileNotFoundError(f"Seeds file not found: {file_path}")

    seeds = []

    async with aiofiles.open(file_path, encoding="utf-8") as f:
        content = await f.read()
        lines = content.strip().split("\n")

    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        try:
            seed = parse_seed_line(line)
            if seed:
                seeds.append(seed)
            else:
                logger.warning(f"Invalid seed at line {line_num}: {line}")
        except Exception as e:
            logger.error(f"Error parsing line {line_num}: {e}")

    logger.info(f"Loaded {len(seeds)} seeds from {file_path}")
    return seeds


def parse_seed_line(line: str) -> dict[str, Any] | None:
    """
    Parse a single seed line.

    Args:
        line: Line to parse

    Returns:
        Parsed seed dictionary or None if invalid
    """
    line = line.strip()

    # Try JSON format first
    if line.startswith("{") and line.endswith("}"):
        try:
            # Try parsing as proper JSON
            seed = json.loads(line)
            if "url" in seed:
                return seed
        except json.JSONDecodeError:
            try:
                # Try fixing common JSON issues (unquoted keys)
                # Convert {key: "value"} to {"key": "value"}
                fixed_line = re.sub(r"(\w+):", r'"\1":', line)
                # Convert single quotes to double quotes
                fixed_line = fixed_line.replace("'", '"')
                seed = json.loads(fixed_line)
                if "url" in seed:
                    return seed
            except json.JSONDecodeError:
                pass

    # Try plain URL format
    if line.startswith(("http://", "https://")):
        return {"url": line}

    return None
