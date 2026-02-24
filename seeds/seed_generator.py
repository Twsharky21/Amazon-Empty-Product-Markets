"""
Seed Generator — Produces prioritized query seeds for Amazon autocomplete.

Strategy: Start with short, broad queries that Amazon actually has autocomplete
data for, then let the scraper's recursive branching discover specific niches.

Key design decisions:
    - Puzzle types ordered by popularity (high-volume types first)
    - Short 2-3 word seeds that match real search behavior
    - No 3+ component combos (let autocomplete discover those)
    - ~800-1200 total seeds instead of 48K+ (quality over quantity)
"""

import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Component Lists (ordered by estimated search volume)
# ---------------------------------------------------------------------------

PUZZLE_TYPES = [
    # High volume — these are the big sellers on KDP
    "word search", "crossword", "sudoku", "maze", "activity book",
    "puzzle book", "word find", "brain teaser", "trivia",
    # Medium volume
    "dot to dot", "word scramble", "cryptogram", "number search",
    "logic puzzle", "hidden word", "riddle book",
    # Niche / lower volume
    "acrostic", "kakuro", "kenken", "nonogram", "picture puzzle",
    "rebus puzzle",
]

AUDIENCES = [
    "kids", "adults", "seniors", "teens", "women", "men", "boys", "girls",
    "toddlers", "elderly", "beginners", "experts", "students", "teachers",
    "couples", "families",
]

THEMES = [
    "animals", "sports", "bible", "travel", "food", "nature", "science",
    "history", "music", "movies", "holidays", "christmas", "halloween",
    "easter", "space", "ocean", "dinosaurs", "dogs", "cats", "horses",
    "cars", "military", "nursing", "gardening", "cooking", "fishing",
    "camping", "yoga", "disney", "harry potter", "spanish", "french",
    "german", "japanese", "math", "geography", "usa", "football",
    "baseball", "basketball", "soccer", "golf", "horror", "mystery",
    "fantasy", "flowers", "birds", "farm", "beach", "winter", "summer",
    "spring", "fall autumn", "birthday", "wedding", "baby shower",
    "retirement", "teacher appreciation",
]

MODIFIERS = [
    "large print", "easy", "hard", "giant", "relaxing", "fun",
    "challenging", "simple", "big", "small", "spiral bound",
    "pocket size", "jumbo", "mini", "deluxe",
]

AGE_RANGES = [
    "ages 3-5", "ages 4-8", "ages 6-8", "ages 8-10",
    "ages 8-12", "ages 9-12", "ages 10-14",
]

# Top themes/audiences/modifiers to pair with puzzle types.
# We don't need every combo — just enough to prime the autocomplete.
TOP_AUDIENCES = ["kids", "adults", "seniors", "teens", "women", "men"]
TOP_THEMES = [
    "animals", "bible", "sports", "christmas", "halloween", "disney",
    "nature", "travel", "dogs", "cats", "space", "dinosaurs", "food",
    "history", "science",
]
TOP_MODIFIERS = ["large print", "easy", "hard"]


def generate_seeds() -> list[str]:
    """
    Generate prioritized seed queries for Amazon autocomplete scraping.

    Tier 1 — Bare puzzle types (highest value, always return results):
        "{puzzle_type}"
        "{puzzle_type} book"
        "{puzzle_type} books"
        "{puzzle_type} puzzle book"

    Tier 2 — Puzzle + audience (high value):
        "{puzzle_type} for {audience}"
        "{puzzle_type} book for {audience}"

    Tier 3 — Puzzle + top theme (medium value):
        "{puzzle_type} {theme}"

    Tier 4 — Puzzle + top modifier (medium value):
        "{puzzle_type} {modifier}"
        "{puzzle_type} book {modifier}"

    Tier 5 — Puzzle + age range:
        "{puzzle_type} for {age_range}"
        "{puzzle_type} book for {age_range}"

    Tier 6 — Audience + theme combos (no puzzle type, discovers cross-cutting):
        "{audience} puzzle book"
        "{theme} puzzle book"

    Returns a deduplicated list ordered by tier priority.
    """
    # Use a list to preserve priority order, dedup at the end
    ordered_seeds: list[str] = []
    seen: set[str] = set()

    def _add(query: str) -> None:
        q = query.strip().lower()
        if q and q not in seen:
            seen.add(q)
            ordered_seeds.append(q)

    # --- Tier 1: Bare puzzle types ---
    for pt in PUZZLE_TYPES:
        _add(pt)
        if "book" not in pt:
            _add(f"{pt} book")
            _add(f"{pt} books")
            _add(f"{pt} puzzle book")
        else:
            # Already contains "book" (e.g., "puzzle book", "activity book")
            _add(f"{pt}s")  # plural

    # --- Tier 2: Puzzle + audience ---
    for pt in PUZZLE_TYPES:
        for aud in TOP_AUDIENCES:
            _add(f"{pt} for {aud}")
            if "book" not in pt:
                _add(f"{pt} book for {aud}")

    # --- Tier 3: Puzzle + top themes ---
    for pt in PUZZLE_TYPES:
        for theme in TOP_THEMES:
            _add(f"{pt} {theme}")

    # --- Tier 4: Puzzle + top modifiers ---
    for pt in PUZZLE_TYPES:
        for mod in TOP_MODIFIERS:
            _add(f"{pt} {mod}")
            if "book" not in pt:
                _add(f"{pt} book {mod}")

    # --- Tier 5: Puzzle + age ranges ---
    for pt in PUZZLE_TYPES:
        for age in AGE_RANGES:
            _add(f"{pt} for {age}")
            if "book" not in pt:
                _add(f"{pt} book for {age}")

    # --- Tier 6: Cross-cutting discovery ---
    for aud in AUDIENCES:
        _add(f"{aud} puzzle book")
        _add(f"puzzle book for {aud}")
    for theme in TOP_THEMES:
        _add(f"{theme} puzzle book")
        _add(f"{theme} activity book")
        _add(f"{theme} word search")

    logger.info("Generated %d unique seed queries", len(ordered_seeds))
    return ordered_seeds


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seeds = generate_seeds()
    print(f"Total seeds: {len(seeds)}")
    print("\nFirst 30:")
    for s in seeds[:30]:
        print(f"  {s}")
    print("\n...")
    print(f"\nLast 10:")
    for s in seeds[-10:]:
        print(f"  {s}")
