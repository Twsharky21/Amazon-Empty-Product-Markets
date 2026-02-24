"""
Seed Generator — Produces all base query combinations for Amazon autocomplete.

Builds queries from combinations of puzzle types, audiences, themes, modifiers,
and age ranges using predefined templates.
"""

import logging
from itertools import product as iterproduct

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Component Lists
# ---------------------------------------------------------------------------

PUZZLE_TYPES = [
    "word search", "crossword", "sudoku", "cryptogram", "maze",
    "word scramble", "number search", "logic puzzle", "word find",
    "brain teaser", "dot to dot", "hidden word", "acrostic", "kakuro",
    "kenken", "nonogram", "picture puzzle", "rebus puzzle", "trivia",
    "riddle book", "activity book", "puzzle book",
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


def generate_seeds() -> list[str]:
    """
    Generate all seed queries from component combinations.

    Templates:
        1.  "{puzzle_type} book"
        2.  "{puzzle_type} book for {audience}"
        3.  "{puzzle_type} book for {audience} {modifier}"
        4.  "{puzzle_type} book about {theme}"
        5.  "{puzzle_type} book {theme}"
        6.  "{puzzle_type} book {modifier}"
        7.  "{puzzle_type} for {audience} {theme}"
        8.  "{puzzle_type} {theme} for {audience}"
        9.  "{puzzle_type} book for {age_range}"
        10. "{puzzle_type} {modifier}"

    Returns a deduplicated, sorted list of query strings.
    """
    seeds: set[str] = set()

    for pt in PUZZLE_TYPES:
        # Template 1
        seeds.add(f"{pt} book")

        for aud in AUDIENCES:
            # Template 2
            seeds.add(f"{pt} book for {aud}")
            for mod in MODIFIERS:
                # Template 3
                seeds.add(f"{pt} book for {aud} {mod}")

        for theme in THEMES:
            # Template 4
            seeds.add(f"{pt} book about {theme}")
            # Template 5
            seeds.add(f"{pt} book {theme}")

        for mod in MODIFIERS:
            # Template 6
            seeds.add(f"{pt} book {mod}")
            # Template 10
            seeds.add(f"{pt} {mod}")

        for aud in AUDIENCES:
            for theme in THEMES:
                # Template 7
                seeds.add(f"{pt} for {aud} {theme}")
                # Template 8
                seeds.add(f"{pt} {theme} for {aud}")

        for age in AGE_RANGES:
            # Template 9
            seeds.add(f"{pt} book for {age}")

    result = sorted(seeds)
    logger.info("Generated %d unique seed queries", len(result))
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seeds = generate_seeds()
    print(f"Total seeds: {len(seeds)}")
    for s in seeds[:20]:
        print(f"  {s}")
    print("  ...")
