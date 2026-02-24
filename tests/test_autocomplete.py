"""Tests for autocomplete scraper (with mocked HTTP)."""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper.autocomplete import _fetch_suggestions, scrape_autocomplete
from scraper.rate_limiter import RateLimiter


def _make_mock_response(suggestions: list[str], status_code: int = 200):
    """Create a mock requests.Response."""
    mock = MagicMock()
    mock.status_code = status_code
    mock.raise_for_status = MagicMock()
    if status_code >= 400:
        mock.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
    mock.json.return_value = {
        "suggestions": [{"value": s} for s in suggestions]
    }
    return mock


def test_fetch_suggestions_success():
    rl = RateLimiter(min_delay=0.001, max_delay=0.002)
    session = MagicMock()
    session.get.return_value = _make_mock_response(["word search book", "word search for kids"])

    result = _fetch_suggestions("word search", rl, session, timeout=5)

    assert result == ["word search book", "word search for kids"]
    assert rl.consecutive_failures == 0


def test_fetch_suggestions_failure():
    rl = RateLimiter(min_delay=0.001, max_delay=0.002)
    session = MagicMock()
    session.get.side_effect = Exception("Connection error")

    result = _fetch_suggestions("word search", rl, session, timeout=5)

    assert result == []
    assert rl.consecutive_failures == 1


def test_scrape_saves_results():
    """Test that scrape_autocomplete saves results and handles basic flow."""
    rl = RateLimiter(min_delay=0.001, max_delay=0.002)

    mock_response = _make_mock_response(["sudoku book easy", "sudoku book hard"])

    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "raw.json"

        with patch("scraper.autocomplete.RateLimiter", return_value=rl):
            with patch("requests.Session") as MockSession:
                MockSession.return_value.get.return_value = mock_response

                results = scrape_autocomplete(
                    ["sudoku book"],
                    out_path,
                    max_depth=0,  # No branching for test speed
                )

        assert len(results) >= 1
        assert out_path.exists()

        with open(out_path) as f:
            saved = json.load(f)
        assert len(saved) >= 1
        assert saved[0]["query"] == "sudoku book"


def test_scrape_resume_skips_completed():
    """Test that previously completed queries are skipped on resume."""
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "raw.json"
        progress_path = Path(tmpdir) / "progress.json"

        # Simulate prior progress
        progress = {
            "completed_queries": ["sudoku book"],
            "results": [
                {
                    "query": "sudoku book",
                    "suggestions": ["sudoku book easy"],
                    "timestamp": "2025-01-01T00:00:00",
                    "depth": 0,
                }
            ],
        }
        with open(progress_path, "w") as f:
            json.dump(progress, f)

        mock_response = _make_mock_response(["maze book for kids"])

        with patch("scraper.autocomplete.RateLimiter") as MockRL:
            mock_rl = RateLimiter(min_delay=0.001, max_delay=0.002)
            MockRL.return_value = mock_rl
            with patch("requests.Session") as MockSession:
                MockSession.return_value.get.return_value = mock_response

                results = scrape_autocomplete(
                    ["sudoku book", "maze book"],
                    out_path,
                    max_depth=0,
                    progress_path=progress_path,
                )

        # Should have 2 results: 1 from resume + 1 new
        assert len(results) == 2
