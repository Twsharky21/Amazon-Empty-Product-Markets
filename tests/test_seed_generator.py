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


def test_seed_count_is_reasonable():
    """Should generate hundreds of focused queries, not tens of thousands."""
    seeds = generate_seeds()
    assert 500 < len(seeds) < 2000, f"Got {len(seeds)} seeds — expected 500-2000"


def test_no_book_book_duplicates():
    """Types containing 'book' should not produce 'book book' queries."""
    seeds = generate_seeds()
    bad = [s for s in seeds if "book book" in s]
    assert len(bad) == 0, f"Found 'book book' dupes: {bad[:5]}"


def test_priority_order_high_volume_first():
    """High-volume puzzle types should appear before niche ones."""
    seeds = generate_seeds()
    word_search_idx = next(i for i, s in enumerate(seeds) if s == "word search")
    acrostic_idx = next(i for i, s in enumerate(seeds) if s == "acrostic")
    assert word_search_idx < acrostic_idx, "word search should come before acrostic"


def test_tier1_bare_types_present():
    """Tier 1: bare puzzle type queries."""
    seeds = generate_seeds()
    assert "word search" in seeds
    assert "crossword" in seeds
    assert "sudoku" in seeds
    assert "word search book" in seeds
    assert "sudoku books" in seeds


def test_tier2_audience_combos_present():
    """Tier 2: puzzle + audience."""
    seeds = generate_seeds()
    assert "word search for kids" in seeds
    assert "crossword for adults" in seeds
    assert "sudoku for seniors" in seeds


def test_tier3_theme_combos_present():
    """Tier 3: puzzle + theme."""
    seeds = generate_seeds()
    assert "word search animals" in seeds
    assert "crossword bible" in seeds
    assert "sudoku christmas" in seeds


def test_tier4_modifier_combos_present():
    """Tier 4: puzzle + modifier."""
    seeds = generate_seeds()
    assert "word search large print" in seeds
    assert "sudoku easy" in seeds


def test_tier5_age_range_present():
    """Tier 5: puzzle + age range."""
    seeds = generate_seeds()
    assert "maze for ages 4-8" in seeds


def test_tier6_cross_cutting_present():
    """Tier 6: audience/theme + generic puzzle book."""
    seeds = generate_seeds()
    assert "kids puzzle book" in seeds
    assert "puzzle book for adults" in seeds
    assert "animals puzzle book" in seeds


def test_all_puzzle_types_represented():
    seeds = generate_seeds()
    seeds_joined = " | ".join(seeds)
    for pt in PUZZLE_TYPES:
        assert pt in seeds_joined, f"Puzzle type '{pt}' not found in any seed"


def test_seeds_are_short():
    """Most seeds should be 2-4 words to match real search behavior."""
    seeds = generate_seeds()
    long_seeds = [s for s in seeds if len(s.split()) > 5]
    pct_long = len(long_seeds) / len(seeds) * 100
    assert pct_long < 15, f"{pct_long:.0f}% of seeds are >5 words — too many long queries"
