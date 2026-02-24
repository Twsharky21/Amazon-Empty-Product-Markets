"""
Categorizer — Tags each suggestion by puzzle type, audience, theme, modifier, age range.

Uses simple keyword/string matching against the known seed component lists.
"""

import json
import logging
from pathlib import Path

from seeds.seed_generator import (
    AGE_RANGES,
    AUDIENCES,
    MODIFIERS,
    PUZZLE_TYPES,
    THEMES,
)

logger = logging.getLogger(__name__)


def _find_matches(text: str, candidates: list[str]) -> list[str]:
    """Return all candidates found as substrings in text."""
    lower = text.lower()
    return [c for c in candidates if c.lower() in lower]


def categorize_suggestion(text: str) -> dict:
    """
    Tag a single suggestion with its attributes.

    Returns dict with keys:
        suggestion, puzzle_types, audiences, themes, modifiers, age_ranges
    """
    return {
        "suggestion": text,
        "puzzle_types": _find_matches(text, PUZZLE_TYPES) or ["unknown"],
        "audiences": _find_matches(text, AUDIENCES) or ["general"],
        "themes": _find_matches(text, THEMES) or ["none"],
        "modifiers": _find_matches(text, MODIFIERS) or ["none"],
        "age_ranges": _find_matches(text, AGE_RANGES) or ["none"],
    }


def categorize(
    cleaned_path: Path,
    output_path: Path,
) -> list[dict]:
    """
    Categorize all cleaned suggestions.

    Args:
        cleaned_path: Path to deduplicated JSON.
        output_path: Path to write categorized data (JSON).

    Returns:
        List of categorized suggestion dicts.
    """
    with open(cleaned_path, "r", encoding="utf-8") as f:
        cleaned = json.load(f)

    categorized = []
    for item in cleaned:
        entry = categorize_suggestion(item["suggestion"])
        entry["frequency"] = item["frequency"]
        categorized.append(entry)

    logger.info("Categorized %d suggestions", len(categorized))

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(categorized, f, indent=2)

    return categorized
