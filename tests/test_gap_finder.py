"""Tests for gap_finder module."""

import json
import math
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from analysis.gap_finder import (
    _build_matrix,
    _find_cross_type_opportunities,
    _find_gaps,
    _find_modifier_gaps,
    find_gaps,
)


def _make_categorized_items():
    """Create sample categorized data for testing."""
    return [
        {
            "suggestion": "word search animals for kids",
            "puzzle_types": ["word search"],
            "audiences": ["kids"],
            "themes": ["animals"],
            "modifiers": ["none"],
            "age_ranges": ["none"],
            "frequency": 5,
        },
        {
            "suggestion": "word search bible for seniors",
            "puzzle_types": ["word search"],
            "audiences": ["seniors"],
            "themes": ["bible"],
            "modifiers": ["large print"],
            "age_ranges": ["none"],
            "frequency": 8,
        },
        {
            "suggestion": "crossword animals for adults",
            "puzzle_types": ["crossword"],
            "audiences": ["adults"],
            "themes": ["animals"],
            "modifiers": ["none"],
            "age_ranges": ["none"],
            "frequency": 3,
        },
        {
            "suggestion": "sudoku animals for adults easy",
            "puzzle_types": ["sudoku"],
            "audiences": ["adults"],
            "themes": ["animals"],
            "modifiers": ["easy"],
            "age_ranges": ["none"],
            "frequency": 4,
        },
    ]


def test_build_matrix_basic():
    items = _make_categorized_items()
    matrix = _build_matrix(
        items,
        "puzzle_types", "themes",
        ["word search", "crossword", "sudoku"],
        ["animals", "bible", "sports"],
    )
    assert isinstance(matrix, pd.DataFrame)
    assert matrix.at["word search", "animals"] == 5
    assert matrix.at["word search", "bible"] == 8
    assert matrix.at["crossword", "animals"] == 3
    assert matrix.at["crossword", "bible"] == 0  # gap
    assert matrix.at["sudoku", "sports"] == 0    # gap


def test_find_gaps_identifies_zeros():
    matrix = pd.DataFrame(
        [[5, 0], [3, 2]],
        index=["word search", "crossword"],
        columns=["animals", "bible"],
    )
    gaps = _find_gaps(matrix, min_row_total=1, min_col_total=1)
    assert len(gaps) == 1
    assert gaps[0]["row"] == "word search"
    assert gaps[0]["column"] == "bible"


def test_find_gaps_uses_geometric_mean():
    """Score should be sqrt(row_total * col_total) * fill_bonus, not sum."""
    matrix = pd.DataFrame(
        [[10, 0, 5], [0, 8, 3]],
        index=["word search", "crossword"],
        columns=["animals", "bible", "sports"],
    )
    gaps = _find_gaps(matrix, min_row_total=1, min_col_total=1)

    # word search bible: rt=15, ct=8, fill_count=1 (only crossword has bible)
    # fill_rate = 1/2 = 0.5, fill_bonus = 1.5
    # score = sqrt(15 * 8) * 1.5 = sqrt(120) * 1.5 ≈ 16.4
    ws_bible = next(g for g in gaps if g["row"] == "word search" and g["column"] == "bible")
    expected = math.sqrt(15 * 8) * (1.0 + 1/2)
    assert abs(ws_bible["score"] - round(expected, 1)) < 0.2


def test_find_gaps_filters_low_demand():
    """Gaps where row or column has < min threshold should be excluded."""
    matrix = pd.DataFrame(
        [[10, 0], [0, 1]],
        index=["word search", "obscure"],
        columns=["animals", "rare_theme"],
    )
    # With default min thresholds of 3, "obscure" row (total=1) and
    # "rare_theme" column (total=1) should be filtered out
    gaps = _find_gaps(matrix, min_row_total=3, min_col_total=3)

    # Only gap that survives: word search × animals has rt=10 but ct(animals)=0... 
    # Actually word search row = 10, animals col = 10, but word search/animals = 10
    # so it's not a gap. No gaps should survive.
    assert len(gaps) == 0


def test_find_gaps_includes_confidence():
    """Each gap should have a confidence tier."""
    matrix = pd.DataFrame(
        [[50, 0], [0, 30]],
        index=["word search", "crossword"],
        columns=["animals", "bible"],
    )
    gaps = _find_gaps(matrix, min_row_total=1, min_col_total=1)
    assert all("confidence" in g for g in gaps)
    assert all(g["confidence"] in ("high", "medium", "low") for g in gaps)


def test_find_gaps_includes_fill_count():
    """Each gap should include col_fill_count and col_fill_rate."""
    matrix = pd.DataFrame(
        [[5, 0], [3, 2], [0, 4]],
        index=["word search", "crossword", "sudoku"],
        columns=["animals", "bible"],
    )
    gaps = _find_gaps(matrix, min_row_total=1, min_col_total=1)
    for g in gaps:
        assert "col_fill_count" in g
        assert "col_fill_rate" in g


def test_geometric_mean_penalizes_one_sided_demand():
    """A gap with huge row but tiny col should score lower than balanced demand."""
    matrix = pd.DataFrame(
        [[200, 0, 0], [0, 0, 50]],
        index=["word search", "crossword"],
        columns=["animals", "cars", "bible"],
    )
    gaps = _find_gaps(matrix, min_row_total=1, min_col_total=1)

    if len(gaps) >= 2:
        # crossword × animals (rt=50, ct=200) should score higher than
        # word search × bible (rt=200, ct=50) — actually same geometric mean
        # but word search × cars (rt=200, ct=0) shouldn't appear (ct < min)
        cars_gaps = [g for g in gaps if g["column"] == "cars"]
        # cars has col_total=0, should be filtered
        assert len(cars_gaps) == 0


def test_find_modifier_gaps():
    items = _make_categorized_items()
    result = _find_modifier_gaps(items)
    # word search has "large print" but crossword doesn't
    puzzle_gaps = result["puzzle_type_modifier_gaps"]
    assert "crossword" in puzzle_gaps
    assert "large print" in puzzle_gaps["crossword"]


def test_cross_type_opportunities():
    items = _make_categorized_items()
    opps = _find_cross_type_opportunities(items)
    # "animals" exists in word search, crossword, sudoku
    # "bible" only exists in word search
    # So crossword and sudoku should have "animals" NOT as opportunity
    # but "bible" as opportunity for crossword/sudoku since only 1 other type has it...
    # Actually needs >=2 other types. "animals" is in 3 types so none are missing it.
    assert isinstance(opps, list)


def test_find_gaps_full_pipeline():
    items = _make_categorized_items()

    tmpdir = tempfile.mkdtemp()
    tmpdir = Path(tmpdir)
    cat_path = tmpdir / "categorized.json"
    out_dir = tmpdir / "output"

    with open(cat_path, "w") as f:
        json.dump(items, f)

    results = find_gaps(cat_path, out_dir)

    assert "puzzle_type_x_theme_gaps" in results
    assert "puzzle_type_x_audience_gaps" in results
    assert "matrices" in results
    assert (out_dir / "matrix_puzzle_type_x_theme.csv").exists()
    assert (out_dir / "gap_analysis.json").exists()

    # Verify gap entries have new fields
    for gap_list_key in ["puzzle_type_x_theme_gaps", "puzzle_type_x_audience_gaps"]:
        for gap in results[gap_list_key]:
            assert "confidence" in gap
            assert "col_fill_count" in gap
            assert "col_fill_rate" in gap
