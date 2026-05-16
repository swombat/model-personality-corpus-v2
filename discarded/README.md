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
