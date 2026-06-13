# Release notes — v1.2.7

Prepared 2026-06-13.

## Added

- Added Kimi K2.7-code direct cell via the Kimi coding endpoint:
  - Model ID: `kimi-k2.7-code`
  - Canonical cell label: `kimi-k2-7-code-direct`
- Added MiniMax M3 direct cell via the MiniMax direct endpoint:
  - Model ID: `MiniMax-M3`
  - Canonical cell label: `minimax-m3-direct`
- Collected full Corpus V2 coverage for both cells:
  - Freeflow: 125/125 valid samples per cell (25 each for LONG, MID, SHORT, OPEN, VARY).
  - Values: 120/120 valid samples per cell (CTRL1/2/3 ×10, G1/2/3 ×30).

## Collection note

- MiniMax M3 is reasoning-capable. The direct MiniMax caller now sends `thinking: {"type": "disabled"}` for `MiniMax-M3` so corpus traces record final response text rather than reasoning scratchpad.

## Regenerated

- `data/CORPUS_SUMMARY.md`
- `data/MATRIX.md`
- `tables/cells.tsv`
- `tables/summary.md`

## Corpus totals

- Freeflow: 19,420 valid samples across 195 cells.
- Values: 15,466 valid samples across 129 cells.
- Combined: 34,886 valid samples across 324 cells and 71 distinct models.
