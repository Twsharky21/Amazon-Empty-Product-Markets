"""
Autocomplete Scraper — Hits Amazon's suggestion endpoint and collects results.

Supports recursive branching (appending a-z to discovered suggestions) up to
a configurable depth, incremental saves, and resumption from partial runs.
"""

import json
import logging
import string
from datetime import datetime, timezone
from pathlib import Path

import requests

from .rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

AUTOCOMPLETE_URL = "https://completion.amazon.com/api/2017/suggestions"
DEFAULT_PARAMS = {
    "mid": "ATVPDKIKX0DER",  # Amazon US marketplace
    "alias": "aps",            # All departments
}


def _fetch_suggestions(
    query: str,
    rate_limiter: RateLimiter,
    session: requests.Session,
    timeout: int = 10,
) -> list[str]:
    """
    Fetch autocomplete suggestions for a single query.

    Returns a list of suggestion strings, or an empty list on failure.
    """
    headers = {
        "User-Agent": rate_limiter.get_user_agent(),
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
    }
    params = {**DEFAULT_PARAMS, "prefix": query}

    try:
        rate_limiter.wait()
        resp = session.get(
            AUTOCOMPLETE_URL,
            params=params,
            headers=headers,
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()

        suggestions = []
        for item in data.get("suggestions", []):
            value = item.get("value", "").strip()
            if value:
                suggestions.append(value)

        rate_limiter.record_success()
        return suggestions

    except (requests.RequestException, OSError, ConnectionError) as exc:
        rate_limiter.record_failure()
        logger.error("Request failed for query '%s': %s", query, exc)
        return []
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        rate_limiter.record_failure()
        logger.error("Parse error for query '%s': %s", query, exc)
        return []
    except Exception as exc:
        rate_limiter.record_failure()
        logger.error("Unexpected error for query '%s': %s", query, exc)
        return []


def _load_progress(progress_path: Path) -> dict:
    """Load previously saved progress file."""
    if progress_path.exists():
        with open(progress_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"completed_queries": [], "results": []}


def _save_progress(progress_path: Path, progress: dict) -> None:
    """Incrementally save progress to disk."""
    with open(progress_path, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2)


def scrape_autocomplete(
    seed_queries: list[str],
    output_path: Path,
    max_depth: int = 2,
    max_failures: int = 10,
    progress_path: Path | None = None,
) -> list[dict]:
    """
    Scrape Amazon autocomplete for all seed queries with recursive branching.

    Args:
        seed_queries: List of base queries to search.
        output_path: Where to save the final raw_suggestions.json.
        max_depth: Maximum recursion depth for branching (0 = seeds only).
        max_failures: Stop after this many consecutive failures.
        progress_path: Path for incremental progress saves (for resumption).

    Returns:
        List of result dicts with keys: query, suggestions, timestamp, depth.
    """
    if progress_path is None:
        progress_path = output_path.parent / "scrape_progress.json"

    progress = _load_progress(progress_path)
    completed = set(progress["completed_queries"])
    results = progress["results"]

    rate_limiter = RateLimiter()
    session = requests.Session()

    # Build work queue: (query, depth)
    queue: list[tuple[str, int]] = [(q, 0) for q in seed_queries if q not in completed]
    total_initial = len(seed_queries)
    logger.info(
        "Starting scrape: %d seeds, %d already completed, %d remaining",
        total_initial,
        len(completed),
        len(queue),
    )

    processed = len(completed)
    interrupted = False

    try:
        while queue:
            query, depth = queue.pop(0)

            if query in completed:
                continue

            suggestions = _fetch_suggestions(query, rate_limiter, session)

            if rate_limiter.consecutive_failures >= max_failures:
                logger.error(
                    "Aborting: %d consecutive failures. Saving progress.",
                    max_failures,
                )
                break

            result = {
                "query": query,
                "suggestions": suggestions,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "depth": depth,
            }
            results.append(result)
            completed.add(query)
            progress["completed_queries"].append(query)

            processed += 1

            # Recursive branching
            if suggestions and depth < max_depth:
                for suggestion in suggestions:
                    for letter in string.ascii_lowercase:
                        branch_query = f"{suggestion} {letter}"
                        if branch_query not in completed:
                            queue.append((branch_query, depth + 1))

            # Save progress every 50 queries
            if processed % 50 == 0:
                _save_progress(progress_path, progress)
                logger.info("Progress saved. Processed %d queries so far.", processed)

    except KeyboardInterrupt:
        interrupted = True
        logger.info("\nInterrupted by user. Saving progress...")

    # Always save progress and write output file
    progress["results"] = results
    _save_progress(progress_path, progress)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    if interrupted:
        logger.info(
            "Progress saved. %d queries completed. Run again to resume, "
            "or use --analyze-only to analyze collected data.",
            processed,
        )
    else:
        logger.info("Scraping complete. %d total results saved to %s", len(results), output_path)

    return results
