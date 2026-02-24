"""
Gap Finder — Identifies underserved niches by analyzing what's missing.

Builds cross-reference matrices (puzzle_type × theme, puzzle_type × audience,
theme × audience) and flags empty cells as potential opportunities. Ranks
opportunities based on demand signals from related queries.
"""

import json
import logging
from collections import defaultdict
from pathlib import Path

import pandas as pd

from seeds.seed_generator import AUDIENCES, MODIFIERS, PUZZLE_TYPES, THEMES

logger = logging.getLogger(__name__)


def _build_matrix(
    categorized: list[dict],
    row_field: str,
    col_field: str,
    row_values: list[str],
    col_values: list[str],
) -> pd.DataFrame:
    """
    Build a count matrix from categorized data.

    Each cell = number of unique suggestions matching that (row, col) combination.
    """
    counts = defaultdict(lambda: defaultdict(int))

    for item in categorized:
        rows = item.get(row_field, [])
        cols = item.get(col_field, [])
        freq = item.get("frequency", 1)
        for r in rows:
            if r in ("unknown", "general", "none"):
                continue
            for c in cols:
                if c in ("unknown", "general", "none"):
                    continue
                counts[r][c] += freq

    df = pd.DataFrame(0, index=row_values, columns=col_values)
    for r in row_values:
        for c in col_values:
            if r in counts and c in counts[r]:
                df.at[r, c] = counts[r][c]

    return df


def _find_gaps(matrix: pd.DataFrame) -> list[dict]:
    """
    Find empty cells in a matrix and score them as opportunities.

    Score = (row_total + col_total) — higher means more demand in
    related areas, so the gap is more interesting.
    """
    row_totals = matrix.sum(axis=1)
    col_totals = matrix.sum(axis=0)
    gaps = []

    for row in matrix.index:
        for col in matrix.columns:
            if matrix.at[row, col] == 0:
                score = int(row_totals.get(row, 0) + col_totals.get(col, 0))
                if score > 0:  # Only flag gaps where there IS some related demand
                    gaps.append({
                        "row": row,
                        "column": col,
                        "score": score,
                        "row_total": int(row_totals.get(row, 0)),
                        "col_total": int(col_totals.get(col, 0)),
                    })

    gaps.sort(key=lambda x: x["score"], reverse=True)
    return gaps


def _find_modifier_gaps(
    categorized: list[dict],
) -> dict:
    """
    Find which puzzle types lack key modifiers (e.g., 'large print')
    and which audiences lack key modifiers (e.g., 'easy').
    """
    key_modifiers = ["large print", "easy", "hard", "giant", "relaxing"]

    puzzle_mod = defaultdict(set)
    audience_mod = defaultdict(set)

    for item in categorized:
        for pt in item.get("puzzle_types", []):
            if pt == "unknown":
                continue
            for mod in item.get("modifiers", []):
                if mod != "none":
                    puzzle_mod[pt].add(mod)
        for aud in item.get("audiences", []):
            if aud == "general":
                continue
            for mod in item.get("modifiers", []):
                if mod != "none":
                    audience_mod[aud].add(mod)

    puzzle_gaps = {}
    for pt in PUZZLE_TYPES:
        existing = puzzle_mod.get(pt, set())
        missing = [m for m in key_modifiers if m not in existing]
        if missing:
            puzzle_gaps[pt] = missing

    audience_gaps = {}
    for aud in AUDIENCES:
        existing = audience_mod.get(aud, set())
        missing = [m for m in key_modifiers if m not in existing]
        if missing:
            audience_gaps[aud] = missing

    return {"puzzle_type_modifier_gaps": puzzle_gaps, "audience_modifier_gaps": audience_gaps}


def _find_cross_type_opportunities(categorized: list[dict]) -> list[dict]:
    """
    Find themes that exist for one puzzle type but not another.
    E.g., 'bible word search' exists but 'bible cryptogram' doesn't.
    """
    type_themes: dict[str, set[str]] = defaultdict(set)
    for item in categorized:
        for pt in item.get("puzzle_types", []):
            if pt == "unknown":
                continue
            for theme in item.get("themes", []):
                if theme != "none":
                    type_themes[pt].add(theme)

    all_themes_seen = set()
    for themes in type_themes.values():
        all_themes_seen.update(themes)

    opportunities = []
    for pt in PUZZLE_TYPES:
        existing = type_themes.get(pt, set())
        for theme in all_themes_seen:
            if theme not in existing:
                # Count how many other puzzle types have this theme
                other_count = sum(
                    1 for other_pt, themes in type_themes.items()
                    if other_pt != pt and theme in themes
                )
                if other_count >= 2:  # Theme is popular in at least 2 other types
                    opportunities.append({
                        "puzzle_type": pt,
                        "theme": theme,
                        "other_types_with_theme": other_count,
                    })

    opportunities.sort(key=lambda x: x["other_types_with_theme"], reverse=True)
    return opportunities


def find_gaps(
    categorized_path: Path,
    output_dir: Path,
) -> dict:
    """
    Run full gap analysis and write results.

    Args:
        categorized_path: Path to categorized JSON.
        output_dir: Directory to write matrix CSVs and gap data.

    Returns:
        Dict with all gap analysis results.
    """
    with open(categorized_path, "r", encoding="utf-8") as f:
        categorized = json.load(f)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Matrix 1: puzzle_type × theme
    pt_theme = _build_matrix(
        categorized, "puzzle_types", "themes", PUZZLE_TYPES, THEMES
    )
    pt_theme.to_csv(output_dir / "matrix_puzzle_type_x_theme.csv")
    pt_theme_gaps = _find_gaps(pt_theme)

    # Matrix 2: puzzle_type × audience
    pt_audience = _build_matrix(
        categorized, "puzzle_types", "audiences", PUZZLE_TYPES, AUDIENCES
    )
    pt_audience.to_csv(output_dir / "matrix_puzzle_type_x_audience.csv")
    pt_audience_gaps = _find_gaps(pt_audience)

    # Matrix 3: theme × audience
    theme_audience = _build_matrix(
        categorized, "themes", "audiences", THEMES, AUDIENCES
    )
    theme_audience.to_csv(output_dir / "matrix_theme_x_audience.csv")
    theme_audience_gaps = _find_gaps(theme_audience)

    # Modifier gaps
    modifier_gaps = _find_modifier_gaps(categorized)

    # Cross-type opportunities
    cross_type = _find_cross_type_opportunities(categorized)

    results = {
        "puzzle_type_x_theme_gaps": pt_theme_gaps[:100],
        "puzzle_type_x_audience_gaps": pt_audience_gaps[:100],
        "theme_x_audience_gaps": theme_audience_gaps[:100],
        "modifier_gaps": modifier_gaps,
        "cross_type_opportunities": cross_type[:100],
        "matrices": {
            "puzzle_type_x_theme": pt_theme,
            "puzzle_type_x_audience": pt_audience,
            "theme_x_audience": theme_audience,
        },
    }

    # Save gap analysis as JSON (without DataFrames)
    json_results = {k: v for k, v in results.items() if k != "matrices"}
    with open(output_dir / "gap_analysis.json", "w", encoding="utf-8") as f:
        json.dump(json_results, f, indent=2)

    logger.info(
        "Gap analysis complete. Found %d puzzle×theme gaps, %d puzzle×audience gaps, "
        "%d theme×audience gaps, %d cross-type opportunities",
        len(pt_theme_gaps),
        len(pt_audience_gaps),
        len(theme_audience_gaps),
        len(cross_type),
    )

    return results
