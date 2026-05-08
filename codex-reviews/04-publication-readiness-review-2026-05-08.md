# Publication-readiness review — 2026-05-08

Scope: review of the current corpus checkout for updated Zenodo publication readiness, with spot checks against the companion `probe-v2`, `product-tier-v2`, and `routing-v2` folders. I treated this as a reviewer pass only; no corpus/prose fixes are included in this file.

## Summary

The raw corpus itself looks structurally sound: JSON parsing succeeds across the trace tree, the canonical summary and analysis scripts run, and the current generated `data/CORPUS_SUMMARY.md` reports a coherent current corpus state:

- Freeflow: 10,345 valid samples across 151 cells.
- Values: 12,468 valid samples across 107 cells.
- Combined: 22,813 valid samples across 258 cells, spanning 49 distinct models.

However, the repository is not yet ready to publish as an updated Zenodo version without metadata/provenance cleanup. The main issue is that top-level publication metadata still describes the older 19,333-sample / 228-cell state, while the data and regenerated corpus summary describe the newer 22,813-sample / 258-cell state.

## Findings

### 1. Blocker: top-level README totals are stale relative to the current data

`README.md:21-29` still advertises:

- 19,333 valid samples
- 228 cells
- values probe: 8,988 valid samples across 77 cells

But `python3 scripts/corpus_summary.py` regenerates `data/CORPUS_SUMMARY.md` with:

- values: 12,468 valid samples across 107 cells
- combined: 22,813 valid samples across 258 cells

This is a direct publication mismatch. A reader landing on Zenodo/GitHub would see the old corpus size while the files contain the expanded values corpus.

### 2. Blocker: `CITATION.cff` still describes the old/older cell count

`CITATION.cff:5-7` says the corpus contains "49 large language models across 226 model-route cells." This is stale even relative to the earlier README state of 228 cells, and now much further from the current generated inventory of 258 cells.

If this checkout is published as a new Zenodo version, `CITATION.cff` should be updated to the new version, date, and corpus-size description.

### 3. Blocker: version/provenance text still says v1.0.2 had no data changes, but the checkout now has new data

`README.md:423-434` presents v1.0.2 as the latest state and says "No data changes vs v1.0.1." That is no longer true for the current checkout if it includes the 30 additional values directories now present relative to `~/dev/contemplative-essayist-probe-v2`.

I compared values directories against `~/dev/contemplative-essayist-probe-v2/data/traces_values/` and found 30 additional values cells in this corpus checkout, including GPT-5.x direct/codex values cells, Gemini/Grok/Qwen/Kimi cells, and coding-direct cells. This is a substantive data expansion, so it needs a new changelog/status entry and likely a new Zenodo version rather than being described as v1.0.2 unchanged data.

### 4. Medium: Group F matrix and n75 table are stale after GPT-5-codex top-up

`data/MATRIX.md:94` still reports `gpt-5-codex-direct` as `24/25 / 23/25 / 25/25 (two timeouts)` with composite `41.3`, and `data/MATRIX.md:102` says Group F has 597 valid samples.

Current trace files show:

- `freeflow_gpt-5-codex-direct`: 25 valid
- `freeflow_gpt-5-codex-direct-r2`: 25 valid
- `freeflow_gpt-5-codex-direct-r3`: 25 valid

Running `python3 scripts/aggregate_n75.py` would update `data/n75_composite_summary.tsv` from n=72 to n=75 for `gpt-5-codex-direct`:

- old checked-in row: 24 / 23 / 25, all_n=72, all_mean=1.722
- regenerated row: 25 / 25 / 25, all_n=75, all_mean=1.773

This is not a huge scientific change, but it is a reproducibility mismatch: the checked-in derived table no longer matches the raw traces and script.

### 5. Medium: companion paper repos still cite the old corpus size

The sibling repositories contain live manuscript/prose references to the older corpus totals. Examples found by search:

- `~/dev/contemplative-essayist-routing-v2/paper.tex` still says 151 freeflow + 77 values = 228 cells and 19,333 valid samples.
- `~/dev/contemplative-essayist-product-tier-v2/paper.tex` still says the full v2 corpus comprises 228 cells / 19,333 valid samples.
- `~/dev/contemplative-essayist-probe-v2/papers/drift/paper.tex`, `papers/routing/paper.tex`, and `papers/product-tier/paper.tex` contain the same older totals.

This is fine only if those papers intentionally cite the frozen v1.0.2 corpus. If the updated Zenodo publication is meant to become the "latest" corpus referenced by the papers, those references need either updating or explicit version scoping.

### 6. Low/clarity: zero-valid values cells are counted as cells with data in coverage wording

`data/CORPUS_SUMMARY.md` reports `kimi-coding` as values partial `(0/120)` because the values directory exists but all 120 files are 401 Unauthorized placeholders. That is mechanically correct under the current script's "directory exists" logic, but publication prose would be clearer if zero-valid cells were described as "no valid values samples" rather than "partial."

Other zero-valid cells found:

- freeflow `deepseek-v4-pro-or`
- freeflow `deepseek-v4-pro-or-pin-deepseek`
- values `deepseek-v4-pro-or-pin-deepseek`
- values `kimi-coding-direct`

These are not blockers as long as the README continues to state that errored/incomplete files are retained for retry bookkeeping and excluded from valid-sample counts.

## Checks Performed

- `python3 -m py_compile scripts/*.py`: passed.
- `python3 scripts/corpus_summary.py`: passed; regenerated current 151 freeflow / 107 values / 258 combined cell inventory.
- `python3 scripts/run_analysis.py`: passed; regenerated freeflow tables, 10,345 valid samples.
- `python3 scripts/analyze_per_provider.py --probe both`: passed; Fireworks and DekaLLM exclusions were applied as documented.
- `python3 scripts/values_route_compare.py`: passed.
- `python3 scripts/aggregate_n75.py`: passed, but revealed the stale checked-in `gpt-5-codex-direct` n75 row noted above.
- `python3 scripts/temporal_substrate.py`: passed.
- Full JSON parse scan over `data/**/*.json`: 0 parse errors.
- Empty/missing `result` placeholders: 702 files, expected bookkeeping/error artifacts excluded from valid counts.
- Pinned OpenRouter route spot check over valid `*-or-pin-*` samples: 15,138 valid pinned samples checked; `raw.provider` matched the pinned provider slug for all checked samples after normalizing provider display names.
- TSV column-width sanity check: `data/*.tsv` and `tables/*.tsv` have consistent row widths.

## Recommendation

Do not publish this checkout to Zenodo as-is. The data and scripts are mostly in good shape, but the release metadata is still describing the prior corpus state. I would treat this as a new data release candidate, update the README/CFF/changelog/matrix/n75 derived table intentionally, and decide whether companion papers should remain pinned to v1.0.2 or move to the expanded corpus version.
