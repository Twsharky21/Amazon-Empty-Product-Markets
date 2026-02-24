"""Tests for report module."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from output.report import generate_reports


def _make_test_data(tmpdir: Path) -> tuple[Path, dict]:
    """Create test categorized data and gap results."""
    categorized = [
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
            "suggestion": "sudoku bible for seniors large print",
            "puzzle_types": ["sudoku"],
            "audiences": ["seniors"],
            "themes": ["bible"],
            "modifiers": ["large print"],
            "age_ranges": ["none"],
            "frequency": 3,
        },
    ]

    cat_path = tmpdir / "categorized.json"
    with open(cat_path, "w") as f:
        json.dump(categorized, f)

    matrix = pd.DataFrame(
        [[5, 0], [0, 3]],
        index=["word search", "sudoku"],
        columns=["animals", "bible"],
    )

    gap_results = {
        "puzzle_type_x_theme_gaps": [
            {"row": "word search", "column": "bible", "score": 10, "row_total": 5, "col_total": 3},
            {"row": "sudoku", "column": "animals", "score": 8, "row_total": 3, "col_total": 5},
        ],
        "puzzle_type_x_audience_gaps": [],
        "theme_x_audience_gaps": [],
        "modifier_gaps": {
            "puzzle_type_modifier_gaps": {"word search": ["easy", "hard"]},
            "audience_modifier_gaps": {"kids": ["large print"]},
        },
        "cross_type_opportunities": [],
        "matrices": {
            "puzzle_type_x_theme": matrix,
            "puzzle_type_x_audience": matrix,
            "theme_x_audience": matrix,
        },
    }

    return cat_path, gap_results


def test_generate_reports_creates_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        cat_path, gap_results = _make_test_data(tmpdir)
        out_dir = tmpdir / "reports"

        generate_reports(cat_path, gap_results, out_dir)

        assert (out_dir / "top_opportunities.txt").exists()
        assert (out_dir / "category_summary.txt").exists()
        assert (out_dir / "raw_clean_data.csv").exists()
        assert (out_dir / "heatmap_puzzle_type_x_theme.png").exists()


def test_opportunities_report_content():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        cat_path, gap_results = _make_test_data(tmpdir)
        out_dir = tmpdir / "reports"

        generate_reports(cat_path, gap_results, out_dir)

        content = (out_dir / "top_opportunities.txt").read_text()
        assert "PUZZLE TYPE x THEME GAPS" in content
        assert "word search" in content
        assert "bible" in content


def test_category_summary_content():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        cat_path, gap_results = _make_test_data(tmpdir)
        out_dir = tmpdir / "reports"

        generate_reports(cat_path, gap_results, out_dir)

        content = (out_dir / "category_summary.txt").read_text()
        assert "PUZZLE TYPES" in content
        assert "word search" in content


def test_raw_csv_content():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        cat_path, gap_results = _make_test_data(tmpdir)
        out_dir = tmpdir / "reports"

        generate_reports(cat_path, gap_results, out_dir)

        df = pd.read_csv(out_dir / "raw_clean_data.csv")
        assert len(df) == 2
        assert "suggestion" in df.columns
        assert "frequency" in df.columns
        assert "puzzle_types" in df.columns
