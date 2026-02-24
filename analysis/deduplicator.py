"""
Deduplicator — Cleans raw autocomplete data.

Removes duplicates, normalizes text, filters non-puzzle-book suggestions,
and counts frequency of each unique suggestion.
"""

import json
import logging
import re
from collections import Counter
from pathlib import Path

from seeds.seed_generator import PUZZLE_TYPES

logger = logging.getLogger(__name__)

# Keywords that indicate a suggestion is puzzle-book related
PUZZLE_KEYWORDS = set(PUZZLE_TYPES) | {
    "puzzle", "word search", "crossword", "sudoku", "maze", "trivia",
    "riddle", "brain teaser", "activity book", "dot to dot", "nonogram",
    "kakuro", "kenken", "cryptogram", "acrostic", "rebus", "word find",
    "word scramble", "number search", "hidden word", "picture puzzle",
    "logic",
}


def _normalize(text: str) -> str:
    """Lowercase, collapse whitespace, strip."""
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def _is_puzzle_related(text: str) -> bool:
    """Check if suggestion is related to puzzle books."""
    lower = text.lower()
    return any(kw in lower for kw in PUZZLE_KEYWORDS)


def deduplicate(
    raw_path: Path,
    output_path: Path,
) -> list[dict]:
    """
    Clean raw autocomplete data.

    Args:
        raw_path: Path to raw_suggestions.json.
        output_path: Path to write cleaned data.

    Returns:
        List of dicts: {"suggestion": str, "frequency": int}
    """
    with open(raw_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    # Collect all suggestions
    all_suggestions: list[str] = []
    for entry in raw_data:
        for suggestion in entry.get("suggestions", []):
            normalized = _normalize(suggestion)
            if normalized:
                all_suggestions.append(normalized)

    logger.info("Total raw suggestions (before dedup): %d", len(all_suggestions))

    # Count frequencies
    counts = Counter(all_suggestions)

    # Filter to puzzle-related and deduplicate
    cleaned = []
    for suggestion, freq in counts.most_common():
        if _is_puzzle_related(suggestion):
            cleaned.append({"suggestion": suggestion, "frequency": freq})

    logger.info("Unique puzzle-related suggestions: %d", len(cleaned))

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2)

    return cleaned
