# Final Publishability Review

Date: 2026-05-03

Reviewer: Codex

Scope: follow-up review after the first round of corpus publishability fixes.

## Summary

The corpus repository is much closer to Zenodo-ready. The major reproducibility issues from the first review appear to be fixed:

- `data/CORPUS_SUMMARY.md` regenerates cleanly.
- `tables/summary.md` and `tables/cells.tsv` regenerate cleanly.
- `tables/per_provider_routing.md`, `tables/per_provider_routing.tsv`, and `tables/per_provider_pairs.tsv` regenerate cleanly, including both freeflow and values sections.
- README sample-schema documentation now matches the actual trace JSON shape.
- Fireworks and DekaLLM exclusions are documented and enforced in `scripts/analyze_per_provider.py`.

I found one remaining consistency issue that should be fixed before publishing the Zenodo release.

## Remaining Blocking Issue

### README still claims a MiniMax M2 Google Vertex effect that is not reproduced by the committed per-provider tables

`README.md` currently says that two robust effects survive multiple-comparison correction:

1. MiniMax M2 on Google Vertex vs MiniMax's own deployment: Cohen's d = 0.73, p < 10^-6.
2. Kimi K2-thinking on AtlasCloud vs Google: d = 0.40, p_Bonferroni = 0.005.

The committed canonical per-provider analysis does reproduce the Kimi effect:

```text
moonshotai/kimi-k2-thinking freeflow atlascloud vs google
t = 3.173, p_raw = 0.001768, p_bonf = 0.005304, q_fdr = 0.005304, d = 0.401
```

However, the committed `tables/per_provider_pairs.tsv` does **not** reproduce a MiniMax M2 Google Vertex vs MiniMax effect. Running:

```bash
python3 scripts/analyze_per_provider.py
```

produces only one Bonferroni-significant comparison across the canonical per-provider tables: the Kimi K2-thinking AtlasCloud vs Google pair above.

The apparent reason is that `scripts/analyze_per_provider.py` currently analyzes `minimax/minimax-m2.7` as the per-provider MiniMax model, using the `minimax-m2-7-*` cells. It does not include the older `minimax/minimax-m2` / `minimax-m2-or-pin-google` vs `minimax-m2-or-pin-minimax` cells that appear to underlie the README's d=0.73 claim.

Suggested fixes, choose one:

1. If the MiniMax M2 Google Vertex effect should remain a headline effect, add the `minimax/minimax-m2` provider-pinned cells to the canonical per-provider analysis and regenerate `tables/per_provider_*`.
2. If the canonical per-provider table should only cover the nine sweep models currently encoded in `scripts/analyze_per_provider.py`, remove or qualify the README claim so it does not say the MiniMax M2 effect survives in the committed canonical tables.
3. If the effect is produced by a separate analysis path, document that path explicitly and make sure it is reproducible from committed scripts/tables.

This is a publication-consistency issue rather than a raw-data issue. The underlying traces appear to be present on disk.

## Checks That Pass

### Corpus summary

Command:

```bash
python3 scripts/corpus_summary.py
git diff --exit-code -- data/CORPUS_SUMMARY.md
```

Result: clean.

Reported corpus state:

- 149 freeflow cells.
- 77 values cells.
- 19,051 valid samples.
- 614 invalid / empty-result placeholders.

### Freeflow analysis tables

Command:

```bash
python3 scripts/run_analysis.py
git diff --exit-code -- tables/summary.md tables/cells.tsv
```

Result: clean.

Reported freeflow analysis state:

- 149 cells.
- 10,063 valid freeflow samples.
- bin distribution: in=137, transitional=6, out=4, no-data=2.

### Per-provider analysis tables

Command:

```bash
python3 scripts/analyze_per_provider.py
git diff --exit-code -- \
  tables/per_provider_routing.md \
  tables/per_provider_routing.tsv \
  tables/per_provider_pairs.tsv
```

Result: clean.

The script now covers both probes by default:

- freeflow
- values

It reports the intended exclusions:

- Fireworks excluded for rate-limit-induced partial collections.
- DekaLLM excluded for response-cache pathology.

### JSON trace structure

Structural validation over `data/traces_freeflow/**/*.json` and `data/traces_values/**/*.json` found:

- 0 JSON parse errors.
- 0 unexpected condition labels.
- 0 filename/JSON condition mismatches.
- 0 label mismatches for files that contain a top-level `label`.
- 19,051 valid samples.
- 614 empty-result placeholders.

### Repository hygiene

No tracked instances were found of:

- `.DS_Store`
- `keys.env`
- logs
- PDFs
- TeX files

The local `.DS_Store` and `codex-reviews/` directory are ignored by `.gitignore`.

The raw provider payloads remain published intentionally and are now documented in the README. This is consistent with the v1 corpus precedent and is not treated as a blocker.

## Minor Non-Blocking Note

`scripts/analyze_per_provider.py` has a stale top docstring usage line:

```text
python scripts/analyze_per_provider.py [--model <or-alias>] [--values]
```

The actual current CLI is:

```text
python scripts/analyze_per_provider.py [--model <or-alias>] [--probe freeflow|values|both]
```

This is not DOI-blocking, but it is worth polishing while fixing the README consistency issue.

## Follow-Up After MiniMax Fix

After commit `0b177779` ("Surface M2-Google-Vertex effect in canonical per-provider tables"), the previous MiniMax/README blocker is resolved:

- `python3 scripts/analyze_per_provider.py` regenerates `tables/per_provider_*` cleanly.
- `minimax/minimax-m2` is included in the canonical per-provider analysis.
- The README headline MiniMax effects match the committed TSV rows:
  - Google vs Novita: d=0.762, p_Bonf=1.455e-07.
  - Google vs MiniMax-self: d=0.659, p_Bonf=5.453e-06.
  - AtlasCloud vs Google: d=-0.564, p_Bonf=0.0001422.
- Kimi K2-thinking AtlasCloud vs Google remains reproduced: d=0.401, p_Bonf=0.005304.

One tiny remaining polish item:

- `scripts/analyze_per_provider.py` has an inline comment near the `minimax/minimax-m2` model entry that still says `d=0.73, google-vertex`. The current canonical rows are d=0.762 for Google vs Novita and d=0.659 for Google vs MiniMax-self. Update that comment to avoid a stale internal breadcrumb.

This is not a data or reproducibility blocker. Once that comment is corrected, I see no remaining publishability issues from this review pass.
