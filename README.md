# Amazon Puzzle Book Niche Finder

Find underserved niches for publishing puzzle books on Amazon KDP by analyzing Amazon's search autocomplete suggestions.

## Quick Start

```bash
pip install -r requirements.txt

# Generate seeds only (no network required)
python main.py --seeds-only

# Run full pipeline (requires network — takes several hours)
python main.py --full

# Analyze existing scraped data
python main.py --analyze-only

# Run tests
pytest tests/ -v
```

## How It Works

1. **Seed Generation** — Creates thousands of search queries from combinations of puzzle types, audiences, themes, and modifiers
2. **Autocomplete Scraping** — Feeds each query to Amazon's suggestion endpoint, then branches deeper by appending a-z to results
3. **Deduplication** — Cleans, normalizes, and counts frequency of suggestions
4. **Categorization** — Tags each suggestion by puzzle type, audience, theme, modifier, and age range
5. **Gap Analysis** — Builds cross-reference matrices and identifies empty cells (missing niches) with high demand signals
6. **Reporting** — Generates ranked opportunity lists, summary stats, CSV exports, and heatmap visualizations

## Output Files

All reports go to `output/reports/`:

| File | Description |
|------|-------------|
| `top_opportunities.txt` | Ranked list of best niche gaps |
| `category_summary.txt` | Suggestion counts per category |
| `raw_clean_data.csv` | Full tagged dataset |
| `matrix_*.csv` | Cross-reference matrices |
| `heatmap_*.png` | Visual density maps |
| `gap_analysis.json` | Machine-readable gap data |

## CLI Options

| Flag | Description |
|------|-------------|
| `--full` | Run everything end to end |
| `--seeds-only` | Just generate seed queries |
| `--scrape-only` | Scrape only (generates seeds if needed) |
| `--analyze-only` | Analyze existing data |
| `--depth N` | Max recursion depth (default: 2) |
| `-v` | Verbose logging |

## Important Notes

- **Rate limiting is built in** — random 1-3s delays between requests with exponential backoff
- **Progress is saved incrementally** — if interrupted, resume where you left off
- **Scraping takes hours** — this is by design to avoid getting blocked by Amazon
- The autocomplete endpoint URL may change over time; check browser dev tools if requests fail
