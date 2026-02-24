"""Tests for categorizer module."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.categorizer import categorize, categorize_suggestion


def test_categorize_word_search_for_seniors():
    result = categorize_suggestion("word search book for seniors large print")
    assert "word search" in result["puzzle_types"]
    assert "seniors" in result["audiences"]
    assert "large print" in result["modifiers"]


def test_categorize_sudoku_animals():
    result = categorize_suggestion("sudoku book about animals for kids")
    assert "sudoku" in result["puzzle_types"]
    assert "animals" in result["themes"]
    assert "kids" in result["audiences"]


def test_categorize_unknown_puzzle():
    result = categorize_suggestion("some random book")
    assert result["puzzle_types"] == ["unknown"]


def test_categorize_general_audience():
    result = categorize_suggestion("word search book")
    assert result["audiences"] == ["general"]


def test_categorize_no_theme():
    result = categorize_suggestion("sudoku book for adults")
    assert result["themes"] == ["none"]


def test_categorize_age_range():
    result = categorize_suggestion("maze book for ages 4-8")
    assert "ages 4-8" in result["age_ranges"]


def test_categorize_multiple_matches():
    result = categorize_suggestion("word search word find puzzle book")
    assert "word search" in result["puzzle_types"]
    assert "word find" in result["puzzle_types"]


def test_categorize_full_pipeline():
    cleaned = [
        {"suggestion": "word search book for seniors", "frequency": 5},
        {"suggestion": "sudoku animals for kids", "frequency": 3},
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        in_path = Path(tmpdir) / "clean.json"
        out_path = Path(tmpdir) / "cat.json"

        with open(in_path, "w") as f:
            json.dump(cleaned, f)

        result = categorize(in_path, out_path)

    assert len(result) == 2
    assert result[0]["frequency"] == 5
    assert "word search" in result[0]["puzzle_types"]
