# Release notes draft — v1.2.0

Prepared: 2026-05-16

## Corpus changes

- Expanded the release corpus to **29,206 valid samples** across **294 cells** and **57 distinct models**.
- Freeflow: **15,420 valid samples** across **179 cells**.
- Values: **13,786 valid samples** across **115 cells**.
- Added/finished N=125 freeflow top-up cells for headline OpenRouter-pinned, Anthropic/direct, coding/direct, Gemini, and Gemma targets.
- Added/finished N=120 values cells for the newly requested Gemini/Gemma additions and other missing target cells.
- Kept all/near-all failed, tiny-failed, and smoke-test non-corpus trace directories under `discarded/`:
  - `discarded/2026-05-16-failed-partial-noncells/MANIFEST.json`
- Moved collection logs under `discarded/`:
  - `discarded/2026-05-16-collection-logs/logs/`

## QA

- Canonical `data/traces_*` tree has restored partial-but-substantive cells; all/near-all failed, tiny-failed, and smoke-test dirs remain under `discarded/`.
- `scripts/run_freeflow_multi.py` and `scripts/run_values_v2.py` now reject error-like result text (e.g. `429`, rate-limit/API/upstream/service-unavailable strings) even if a provider returns it inside an HTTP-200 completion.
- Regenerated `data/CORPUS_SUMMARY.md` after cleanup.
- Regenerated `data/n75_composite_summary.tsv` via `scripts/aggregate_n75.py`.

## Release metadata updated

- `README.md` counts and v1.2.0 release note.
- `CITATION.cff` version/date/counts.
- `data/MATRIX.md` seventh collection round inventory.
- `.gitignore` ignores `logs/`.

## Not done

- Not pushed.
- Not tagged.
- Not committed.
- Awaiting Lume/Daniel review.
