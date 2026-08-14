# Discarded / non-corpus artifacts

This directory preserves collection artifacts that should **not** be counted as
release corpus cells.

The canonical corpus lives under `data/traces_freeflow/` and
`data/traces_values/`. Scripts such as `scripts/corpus_summary.py` scan only
those `data/` trace directories.

Contents:

- `2026-05-16-failed-partial-noncells/` — failed, empty, malformed, or smoke-test
  trace directories removed from the release corpus before the v1.2.0 prep pass.
  See its `MANIFEST.json` for per-cell metrics and reasons.
- `2026-05-16-collection-logs/` — collection-time stdout/log artifacts preserved
  for local review, not corpus data.
- `2026-08-09-local-runtime-smoke-tests/` — 25 Yi-6B MLX compatibility traces
  from a runtime path superseded by the complete official-BF16 Transformers
  collection. Preserved for audit, excluded from release counts.
- `2026-08-13-local-fidelity-rejected/` — six complete-looking local cells
  removed from the canonical corpus after output-fidelity review found raw
  tokenizer markers, leaked continuation-role text, or invalid replacement
  characters. See its `MANIFEST.json`; all six are marked for recollection
  rather than repaired in place.
