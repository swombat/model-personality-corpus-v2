# Release notes — v1.2.4

Prepared: 2026-05-28

## Corpus changes

- Adds `opus-4-8-direct`, a direct Anthropic capture of `claude-opus-4-8` (`Claude Opus 4.8`).
- Anthropic `/v1/models` reported `claude-opus-4-8` with `created_at` 2026-05-28T00:00:00Z at collection time.
- The added cell has complete corpus-v2 coverage: 125/125 valid freeflow samples and 120/120 valid values samples.
- No OpenRouter cell was collected for this release.
- Expanded the release corpus to **33,906 valid samples** across **316 cells** and **67 distinct models**.
- Freeflow: **18,920 valid samples** across **191 cells**.
- Values: **14,986 valid samples** across **125 cells**.

## QA

- Verified the new Opus 4.8 direct cell at full target count with zero malformed/error traces.
- Regenerated `data/CORPUS_SUMMARY.md`.
- Regenerated freeflow analysis tables (`tables/cells.tsv`, `tables/summary.md`); `opus-4-8-direct` composite score is **537** (`in`).
- Updated `data/MATRIX.md`, `README.md`, and `CITATION.cff` release metadata.

## Release status

- Prepared for commit, tag, push, and Zenodo pickup as `v1.2.4`.
