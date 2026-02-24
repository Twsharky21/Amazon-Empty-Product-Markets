"""Tests for deduplicator module."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.deduplicator import _is_puzzle_related, _normalize, deduplicate


def test_normalize_lowercase():
    assert _normalize("Word Search Book") == "word search book"


def test_normalize_strips_whitespace():
    assert _normalize("  word  search   book  ") == "word search book"


def test_is_puzzle_related_true():
    assert _is_puzzle_related("word search book for seniors")
    assert _is_puzzle_related("sudoku large print")
    assert _is_puzzle_related("crossword puzzle book")
    assert _is_puzzle_related("brain teaser for kids")


def test_is_puzzle_related_false():
    assert not _is_puzzle_related("harry potter novel")
    assert not _is_puzzle_related("cooking recipe book")
    assert not _is_puzzle_related("laptop stand")


def test_deduplicate_removes_duplicates():
    raw_data = [
        {"query": "q1", "suggestions": ["Word Search Book", "word search book", "WORD SEARCH BOOK"]},
        {"query": "q2", "suggestions": ["Word Search Book", "sudoku book"]},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        raw_path = Path(tmpdir) / "raw.json"
        out_path = Path(tmpdir) / "clean.json"

        with open(raw_path, "w") as f:
            json.dump(raw_data, f)

        result = deduplicate(raw_path, out_path)

    suggestions = {r["suggestion"] for r in result}
    assert "word search book" in suggestions
    assert "sudoku book" in suggestions


def test_deduplicate_counts_frequency():
    raw_data = [
        {"query": "q1", "suggestions": ["word search book", "word search book"]},
        {"query": "q2", "suggestions": ["word search book"]},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        raw_path = Path(tmpdir) / "raw.json"
        out_path = Path(tmpdir) / "clean.json"

        with open(raw_path, "w") as f:
            json.dump(raw_data, f)

        result = deduplicate(raw_path, out_path)

    ws = next(r for r in result if r["suggestion"] == "word search book")
    assert ws["frequency"] == 3


def test_deduplicate_filters_non_puzzle():
    raw_data = [
        {"query": "q1", "suggestions": ["word search book", "laptop stand", "cooking recipes"]},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        raw_path = Path(tmpdir) / "raw.json"
        out_path = Path(tmpdir) / "clean.json"

        with open(raw_path, "w") as f:
            json.dump(raw_data, f)

        result = deduplicate(raw_path, out_path)

    suggestions = {r["suggestion"] for r in result}
    assert "word search book" in suggestions
    assert "laptop stand" not in suggestions
    assert "cooking recipes" not in suggestions
