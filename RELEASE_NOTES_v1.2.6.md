# Release notes — v1.2.6

Prepared 2026-06-10.

## Added

- Added Anthropic Claude Fable 5 direct cell, verified from Anthropic `/v1/models` as `claude-fable-5` (`Claude Fable 5`, `created_at` 2026-06-07T00:00:00Z).
- New canonical cell label: `fable-5-direct`.
- Collected full Corpus V2 coverage:
  - Freeflow: 125/125 valid samples (25 each for LONG, MID, SHORT, OPEN, VARY).
  - Values: 120/120 valid samples (CTRL1/2/3 ×10, G1/2/3 ×30).

## Regenerated

- `data/CORPUS_SUMMARY.md`
- `tables/cells.tsv`
- `tables/summary.md`

## Corpus totals

- Freeflow: 19,170 valid samples across 193 cells.
- Values: 15,226 valid samples across 127 cells.
- Combined: 34,396 valid samples across 320 cells and 69 distinct models.
