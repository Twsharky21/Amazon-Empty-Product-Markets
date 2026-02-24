"""Tests for seed_generator module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from seeds.seed_generator import (
    AGE_RANGES,
    AUDIENCES,
    MODIFIERS,
    PUZZLE_TYPES,
    THEMES,
    generate_seeds,
)


def test_component_lists_not_empty():
    assert len(PUZZLE_TYPES) >= 20
    assert len(AUDIENCES) >= 15
    assert len(THEMES) >= 50
    assert len(MODIFIERS) >= 10
    assert len(AGE_RANGES) >= 5


def test_generate_seeds_returns_list():
    seeds = generate_seeds()
    assert isinstance(seeds, list)
    assert len(seeds) > 0


def test_generate_seeds_are_unique():
    seeds = generate_seeds()
    assert len(seeds) == len(set(seeds)), "Seeds contain duplicates"


def test_generate_seeds_sorted():
    seeds = generate_seeds()
    assert seeds == sorted(seeds), "Seeds are not sorted"


def test_seed_count_is_substantial():
    """Should generate thousands of queries."""
    seeds = generate_seeds()
    assert len(seeds) > 5000, f"Only {len(seeds)} seeds — expected thousands"


def test_template_1_present():
    """Template: '{puzzle_type} book'"""
    seeds = generate_seeds()
    assert "word search book" in seeds
    assert "sudoku book" in seeds


def test_template_2_present():
    """Template: '{puzzle_type} book for {audience}'"""
    seeds = generate_seeds()
    assert "word search book for seniors" in seeds
    assert "sudoku book for kids" in seeds


def test_template_4_present():
    """Template: '{puzzle_type} book about {theme}'"""
    seeds = generate_seeds()
    assert "crossword book about animals" in seeds


def test_template_9_present():
    """Template: '{puzzle_type} book for {age_range}'"""
    seeds = generate_seeds()
    assert "maze book for ages 4-8" in seeds


def test_all_puzzle_types_represented():
    seeds = generate_seeds()
    seeds_lower = " | ".join(seeds)
    for pt in PUZZLE_TYPES:
        assert pt in seeds_lower, f"Puzzle type '{pt}' not found in any seed"


def test_all_audiences_represented():
    seeds = generate_seeds()
    seeds_lower = " | ".join(seeds)
    for aud in AUDIENCES:
        assert aud in seeds_lower, f"Audience '{aud}' not found in any seed"
