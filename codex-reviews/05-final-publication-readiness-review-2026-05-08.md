# Final publication-readiness review — 2026-05-08

Scope: one final reviewer pass after the v1.1.0 metadata/data updates and the final failed attempt to collect `kimi-coding-direct` values data. I did not make corpus fixes; this file records the review result.

## Verdict

The corpus is very close to Zenodo-ready. I found no raw-data, script, or derived-table reproducibility blockers. The remaining Kimi failure is documented clearly and bounded correctly.

I found one small but visible prose-number mismatch in the README changelog. I would correct that before publication, then I would be comfortable publishing v1.1.0.

## Findings

### 1. Medium: README changelog gives the wrong recomputed GPT-5-codex number

`README.md:538-541` says the `gpt-5-codex-direct` Group F top-up changed:

> `41.3 → 51.7 mean per the regenerated n75_composite_summary.tsv`

That does not match the regenerated artifacts:

- `data/MATRIX.md:94` reports `gpt-5-codex-direct` as 25/25 / 25/25 / 25/25 with composite **44.3**.
- `tables/summary.md` has the three freeflow cell totals as **43**, **43**, and **47**, whose round mean is **44.3**.
- `data/n75_composite_summary.tsv:3` reports per-sample all_mean **1.773**, not 51.7.

So the changelog sentence appears to have the wrong post-top-up composite number. The current data/table state supports **44.3**, not 51.7. This is not a data problem, but it is worth fixing because it is in the public release notes.

## Kimi Failure Review

The failed final Kimi attempt is handled cleanly:

- `README.md:351-407` documents the access-policy-blocked `kimi-coding-direct` values collection, including the 401 failures and provider-policy interpretation.
- `README.md:519-524` records the failed values cell in the v1.1.0 changelog.
- `data/CORPUS_SUMMARY.md:50` marks `kimi-coding` as `values FAILED`, not merely partial.
- `data/CORPUS_SUMMARY.md:71` calls out `kimi-coding` as the one model with a values cell that failed entirely.
- `data/traces_values/kimi-coding-direct/` contains 120 JSON evidence-of-attempt files, all invalid/errored and excluded from valid counts.

This is publication-safe in my view: the failure is transparent, auditable, and excluded from analysis counts.

## Checks Performed

- `git status --short --branch`: only review files are untracked; no tracked corpus diffs remained after the reproducibility runs.
- `python3 -m py_compile scripts/*.py`: passed.
- Full JSON parse scan over `data/**/*.json`: 0 parse errors.
- Empty/missing `result` placeholders: 702 files, concentrated in known failed/excluded cells.
- Independent raw-count scan:
  - freeflow: 10,345 valid samples, 151 cells, 149 non-empty, 67 cells >=50, zero-valid cells `freeflow_deepseek-v4-pro-or` and `freeflow_deepseek-v4-pro-or-pin-deepseek`.
  - values: 12,468 valid samples, 107 cells, 105 non-empty, 104 cells >=50, zero-valid cells `deepseek-v4-pro-or-pin-deepseek` and `kimi-coding-direct`.
- `python3 scripts/corpus_summary.py`: passed and produced no tracked diff.
- `python3 scripts/run_analysis.py`: passed and produced no tracked diff.
- `python3 scripts/analyze_per_provider.py --probe both`: passed and produced no tracked diff; documented Fireworks/DekaLLM exclusions applied.
- `python3 scripts/aggregate_n75.py`: passed and produced no tracked diff.
- `python3 scripts/values_route_compare.py`: passed.
- `python3 scripts/temporal_substrate.py`: passed and produced no tracked diff.
- TSV row-width sanity check over `data/*.tsv` and `tables/*.tsv`: passed.
- Pinned OpenRouter route check: 15,138 valid pinned samples with `raw.provider` checked; 0 provider-pin mismatches after normalizing provider display names.

## Notes

The previous review file `codex-reviews/04-publication-readiness-review-2026-05-08.md` is now historical: its blockers appear to have been addressed in the current checkout. If included in the Zenodo archive, it is superseded by this review.

The companion paper repositories still intentionally cite the v1.0.2 corpus totals per the README's v1.1.0 status note. I did not treat that as a blocker because the current README explicitly says those papers remain pinned to the analytically frozen v1.0.2 corpus unless future revisions choose otherwise.
