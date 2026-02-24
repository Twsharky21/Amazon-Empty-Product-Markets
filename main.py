"""
Amazon Puzzle Book Niche Finder — Main Orchestrator

Runs the full pipeline: seed generation → scraping → dedup → categorization →
gap analysis → reporting.

Usage:
    python main.py --full              # Run everything end to end
    python main.py --seeds-only        # Just generate seed queries
    python main.py --scrape-only       # Scrape using existing seeds
    python main.py --analyze-only      # Analyze existing scraped data
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Project root so imports work
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from seeds.seed_generator import generate_seeds
from scraper.autocomplete import scrape_autocomplete
from analysis.deduplicator import deduplicate
from analysis.categorizer import categorize
from analysis.gap_finder import find_gaps
from output.report import generate_reports

# Paths
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output" / "reports"
SEEDS_PATH = DATA_DIR / "seed_queries.json"
RAW_PATH = DATA_DIR / "raw_suggestions.json"
CLEAN_PATH = DATA_DIR / "clean_suggestions.json"
CATEGORIZED_PATH = DATA_DIR / "categorized_suggestions.json"


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def run_seeds() -> list[str]:
    """Generate and save seed queries."""
    logger = logging.getLogger("main")
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    seeds = generate_seeds()
    with open(SEEDS_PATH, "w", encoding="utf-8") as f:
        json.dump(seeds, f, indent=2)

    logger.info("✓ Generated %d seed queries → %s", len(seeds), SEEDS_PATH)
    return seeds


def run_scrape(max_depth: int = 2) -> None:
    """Run the autocomplete scraper."""
    logger = logging.getLogger("main")

    if not SEEDS_PATH.exists():
        logger.info("No seeds found, generating...")
        run_seeds()

    with open(SEEDS_PATH, "r", encoding="utf-8") as f:
        seeds = json.load(f)

    logger.info("Starting scrape with %d seeds (max_depth=%d)...", len(seeds), max_depth)
    scrape_autocomplete(seeds, RAW_PATH, max_depth=max_depth)
    logger.info("✓ Scraping complete → %s", RAW_PATH)


def run_analysis() -> None:
    """Run the full analysis pipeline on existing scraped data."""
    logger = logging.getLogger("main")

    PROGRESS_PATH = DATA_DIR / "scrape_progress.json"

    # If raw_suggestions.json doesn't exist, build it from progress file
    if not RAW_PATH.exists():
        if PROGRESS_PATH.exists():
            logger.info("No raw_suggestions.json found. Building from scrape_progress.json...")
            with open(PROGRESS_PATH, "r", encoding="utf-8") as f:
                progress = json.load(f)
            results = progress.get("results", [])
            if not results:
                logger.error("Progress file exists but contains no results.")
                sys.exit(1)
            with open(RAW_PATH, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)
            logger.info("Built raw_suggestions.json with %d results from progress file.", len(results))
        else:
            logger.error("No scraped data found. Run scraping first.")
            sys.exit(1)

    # Step 1: Deduplicate
    logger.info("Deduplicating...")
    deduplicate(RAW_PATH, CLEAN_PATH)
    logger.info("✓ Deduplicated → %s", CLEAN_PATH)

    # Step 2: Categorize
    logger.info("Categorizing...")
    categorize(CLEAN_PATH, CATEGORIZED_PATH)
    logger.info("✓ Categorized → %s", CATEGORIZED_PATH)

    # Step 3: Gap analysis
    logger.info("Finding gaps...")
    gap_results = find_gaps(CATEGORIZED_PATH, OUTPUT_DIR)
    logger.info("✓ Gap analysis complete")

    # Step 4: Reports
    logger.info("Generating reports...")
    generate_reports(CATEGORIZED_PATH, gap_results, OUTPUT_DIR)
    logger.info("✓ Reports generated → %s", OUTPUT_DIR)


def run_full(max_depth: int = 2) -> None:
    """Run the complete pipeline end to end."""
    run_seeds()
    run_scrape(max_depth=max_depth)
    run_analysis()


def main():
    parser = argparse.ArgumentParser(
        description="Amazon Puzzle Book Niche Finder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py --full               Run everything
    python main.py --seeds-only         Just generate seed queries
    python main.py --scrape-only        Scrape (generates seeds if needed)
    python main.py --analyze-only       Analyze existing data
    python main.py --full --depth 1     Full run with depth-1 branching
        """,
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--full", action="store_true", help="Run full pipeline")
    mode.add_argument("--seeds-only", action="store_true", help="Generate seeds only")
    mode.add_argument("--scrape-only", action="store_true", help="Scrape only")
    mode.add_argument("--analyze-only", action="store_true", help="Analyze existing data")

    parser.add_argument("--depth", type=int, default=2, help="Max recursion depth (default: 2)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")

    args = parser.parse_args()
    setup_logging(args.verbose)

    if args.seeds_only:
        run_seeds()
    elif args.scrape_only:
        run_scrape(max_depth=args.depth)
    elif args.analyze_only:
        run_analysis()
    elif args.full:
        run_full(max_depth=args.depth)


if __name__ == "__main__":
    main()
