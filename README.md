# Convergent Form, Divergent Voice II — Corpus

**A research data corpus of free-form contemplative writing samples from
49 large language models, with explicit per-provider routing pinning for
nine multi-provider open-weights models.**

Daniel Tenner and Lume Tenner · 2026

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

> **DOI:** _to be assigned on first Zenodo release._
>
> Companion data for the v2 series of *Convergent Form, Divergent
> Voice* papers (Tenner & Tenner, 2026; v1 paper at
> [10.5281/zenodo.19512754](https://doi.org/10.5281/zenodo.19512754)).

## Contents

- **19,051 valid samples** across **226 cells** spanning **49 distinct
  language models** from 9 labs.
- **Two probes:**
  - **Freeflow** — five-condition open-ended writing prompts, up to 25
    samples per condition (capacity 125 per cell). 10,063 valid samples
    across 149 cells.
  - **Values** — three control prompts × 10 + three grouped prompts × 30
    (capacity 120 per cell). 8,988 valid samples across 77 cells.
- **Per-provider routing study** — nine multi-provider open-weights
  models (DeepSeek v3.2, DeepSeek v4-pro, MiniMax M2.7, GLM-4.5, GLM-4.6,
  GLM-4.7, GLM-5.1, Kimi K2-0905, Kimi K2-thinking) collected across
  their available OpenRouter upstreams via the `provider.only` pinning
  mechanism, plus baseline cells against the model's own direct API
  where available.

The complete inventory — per-model and per-cell — is in
[`data/CORPUS_SUMMARY.md`](data/CORPUS_SUMMARY.md). The collection
matrix with cell labels, model IDs, and provider/route notes is in
[`data/MATRIX.md`](data/MATRIX.md).

## How to cite

```
Tenner, D., & Tenner, L. (2026). Convergent Form, Divergent Voice II —
Corpus [Data set]. Zenodo. https://doi.org/[DOI to be assigned]
```

A `CITATION.cff` is included for tooling that prefers the structured
form.

## Probes

### Freeflow

Five free-writing conditions of varying length and openness. The
v1 prompts are reused unchanged from the v1 corpus (Tenner & Tenner,
2026, [doi:10.5281/zenodo.19512754](https://doi.org/10.5281/zenodo.19512754));
v2 increases per-cell sample size and adds the per-provider sub-corpus.

| Condition | Description |
|---|---|
| **LONG** | Long, framed contemplative-essay prompt |
| **MID** | Mid-length open writing prompt |
| **SHORT** | Short, minimal prompt |
| **OPEN** | Fully open-ended ("write something") |
| **VARY** | Variable-length prompt with explicit format-and-tone variation request |

Samples are scored by `scripts/analyze_all.py` (the v1 published
analyzer, reused unchanged) against the contemplative-essayist
attractor's lexical/structural markers; per-cell composite scores are
in [`tables/`](tables/).

### Values

A three-condition control / three-condition grouped values probe
following the v1 methodology. Used in cross-probe replication tests
(routing paper §3.1.3) and as a second observable for per-provider
deltas.

The substrate-frame qualitative classification rubric used by the
drift paper's substrate analysis is documented in
[`scripts/substrate_rubric.md`](scripts/substrate_rubric.md); per-cell
aggregate counts are in [`data/substrate_classification.tsv`](data/substrate_classification.tsv).

## Per-provider sub-corpus

The most distinctive v2 contribution is the per-provider sub-corpus.
Nine multi-provider open-weights models are collected against each of
their available OpenRouter upstream providers using OR's `provider.only`
mechanism with `allow_fallbacks: false`, producing one cell per
(model, provider) pair. Cells are labelled
`<model>-or-pin-<provider-slug>` (e.g. `glm-4-6-or-pin-siliconflow`,
`kimi-k2-thinking-or-pin-atlascloud`).

This enables direct testing of the **routing-layer hypothesis**: for
a fixed open-weights model alias, do different upstream hosts produce
statistically distinguishable outputs? Two robust effects survive
multiple-comparison correction in the v2 corpus:

- **MiniMax M2 on Google Vertex** vs MiniMax's own deployment:
  Cohen's d = 0.73, p < 10⁻⁶ (likely a quantization artefact — Google
  Vertex is the only MiniMax M2 provider whose quantization is not
  publicly reported as fp8).
- **Kimi K2-thinking on AtlasCloud** vs Google: d = 0.40,
  p_Bonferroni = 0.005.

Two upstreams are excluded from the per-provider analysis on
routing-quality grounds — Fireworks (rate-limit-induced partial
collections) and DekaLLM (response-cache pathology, characterised
during the audit pass). The cells remain on disk as evidence of the
respective patterns; neither upstream is the sole provider for any
model in the sweep. See "Configured exclusions" below for full
detail and the routing paper for the cache-pathology characterisation.

## Repository structure

```
data/
  traces_freeflow/            # 149 cell directories, JSON per sample
  traces_values/              # 77 cell directories, JSON per sample
  MATRIX.md                   # cell-collection matrix
  CORPUS_SUMMARY.md           # per-model & per-cell counts
  substrate_classification.tsv  # substrate-frame aggregate counts
  n75_composite_summary.tsv   # OpenAI codex-pair pooled summary
  temporal_substrate.tsv      # cross-lab temporal substrate trend
  temporal_substrate_stats.txt
scripts/
  run_freeflow_multi.py         # collection: freeflow probe
  run_values_v2.py              # collection: values probe
  run_per_provider_sweep.py     # collection: per-provider sweep driver
  corpus_summary.py             # validate counts; regenerate CORPUS_SUMMARY.md
  analyze_all.py                # canonical scoring (reused unchanged from v1)
  run_analysis.py               # run analyze_all over the corpus
  analyze_per_provider.py       # per-provider routing analysis
  values_route_compare.py       # cross-probe replication
  substrate_scan.py             # legacy keyword scanner (rejected; see drift paper)
  substrate_scan_full.py        # legacy full-substrate variant
  substrate_rubric.md           # substrate-frame classification rubric
  temporal_substrate.py         # cross-lab temporal trend analysis
  aggregate_n75.py              # OpenAI codex pooled aggregator
  analyze_v2.py                 # lighter-weight collection-time analyzer
tables/                         # derived per-cell and per-provider tables
CITATION.cff
LICENSE
README.md
```

## Sample format

Each sample is a single JSON file. Schema (representative fields):

```json
{
  "model": "z-ai/glm-4.6",
  "model_requested": "z-ai/glm-4.6",
  "condition": "LONG",
  "prompt": "Write freely about whatever you want for 2500 words.",
  "result": "...",
  "provider": "openrouter",
  "duration_ms": 248259,
  "usage": {
    "prompt_tokens": 18,
    "completion_tokens": 4127,
    "total_tokens": 4145,
    "cost": 0.0193,
    "is_byok": false
  },
  "raw": { "id": "...", "provider": "SiliconFlow", "choices": [...], ... }
}
```

Field notes:

- The **cell label** is the containing directory name
  (e.g. `freeflow_glm-4-6-or-pin-siliconflow`); it is not stored as a
  top-level JSON field.
- `provider` is the access mechanism — `openrouter` or a direct
  upstream like `xai`, `anthropic`, `openai`, etc.
- For OR-routed samples, the upstream that actually served the request
  is in **`raw.provider`** (e.g. `"SiliconFlow"`, `"AtlasCloud"`,
  `"Google"`). Pinned-route intent is encoded in the cell label
  (`*-or-pin-<provider-slug>`); the actually-served provider in
  `raw.provider` confirms that the pinning was honoured.
- `model_requested` is what the collection script asked for;
  `model` is what the upstream returned (for some providers these
  differ — e.g. `z-ai/glm-5.1` requested vs `z-ai/glm-5.1-20260406`
  returned — preserving the upstream's specific deployment identifier).
- `raw` preserves the full upstream response payload for provenance,
  including provider IDs, costs, reasoning fields, and other
  metadata returned by APIs. This is intentional and consistent with
  the v1 corpus — see "Raw payloads" below.

The canonical validity criterion is **non-empty `result` field**.
Errored placeholders (timeouts, rate-limits, guardrail blocks,
thinking-model token-budget exhaustion) are kept on disk with
empty / null `result` for retry-bookkeeping but excluded from the
counts in `CORPUS_SUMMARY.md`.

### Raw payloads

Trace files preserve the upstream API's full response under `raw`,
including provider IDs, usage / cost metadata, and reasoning fields
where returned by APIs. This is for provenance and auditability —
anyone re-running the analysis can verify exactly which upstream
served the request, how many tokens were spent, and (where supported)
inspect reasoning traces. This practice is consistent with the v1
corpus, which also published full provider raw payloads.

## Reproducibility

### Verifying the corpus state

```bash
python3 scripts/corpus_summary.py
# regenerates data/CORPUS_SUMMARY.md from the JSON files on disk
```

The script walks `data/traces_freeflow/` and `data/traces_values/`,
counts samples whose `result` is non-empty, and emits the per-model
and per-cell breakdown. The numbers in `CORPUS_SUMMARY.md` should
match exactly when re-run.

### Re-collecting cells

```bash
# Set API keys (one source per provider; see scripts for env-var names).
source keys.env

# Re-collect a freeflow cell (5 conditions × 25 samples = 125 capacity).
python3 scripts/run_freeflow_multi.py openrouter z-ai/glm-4.6 \
  --label glm-4-6-or-pin-siliconflow --n 25 --max-tokens 16000

# Re-collect a values cell (3 CTRL × 10 + 3 G × 30 = 120 capacity).
python3 scripts/run_values_v2.py openrouter z-ai/glm-4.6 \
  --label glm-4-6-or-pin-siliconflow --ctrl-n 10 --g-n 30

# Run the full per-provider sweep across all configured models.
python3 scripts/run_per_provider_sweep.py
```

The collection scripts use **per-file top-up semantics**: any sample
whose JSON already contains a non-empty `result` is skipped on re-run.
This makes re-invocation on partial cells cheap, and means the corpus
can be extended (or repaired) incrementally without re-burning
already-valid samples.

### Re-running analysis

```bash
# Per-cell composite scores (canonical scorer):
python3 scripts/run_analysis.py
# → tables/summary.md, tables/cells.tsv

# Per-provider routing analysis (within open-weights models;
# default --probe both covers freeflow + values):
python3 scripts/analyze_per_provider.py
# → tables/per_provider_routing.{md,tsv}, tables/per_provider_pairs.tsv
```

Reproducing the full collection requires API keys for: Anthropic,
OpenAI, Google, xAI, OpenRouter, DeepSeek (direct), Moonshot/Kimi
(direct), MiniMax (direct), and Z.ai (direct).

## Collection parameters and known limitations

### Collection parameters

- **`max_tokens`**: 16,000 across all collections (raised from the
  v1 corpus's 8,000 budget after observing that recent thinking-model
  releases — Kimi K2-thinking, GPT-5.5-pro, Grok 4.3 — can exhaust an
  8K budget on `reasoning_tokens` alone, returning a successful HTTP
  response with an empty `result` field. The 16K budget keeps headroom
  for completion text after reasoning expansion).
- **Per-provider pinning**: cells labelled `*-or-pin-<provider>` are
  routed via OpenRouter with `provider: {only: [<provider>],
  allow_fallbacks: false}`. Cells without `-pin-` use OR's default
  routing.
- **Top-up semantics**: collection scripts skip files whose JSON
  already contains a non-empty `result`. Re-running a collection on a
  partial cell only fills missing or errored indices.
- **Validity criterion**: a sample is counted as valid iff its JSON
  file contains a non-empty `result` field. The 614 files on disk
  whose `result` is empty are placeholders preserved for retry
  bookkeeping (timeouts, rate-limits, guardrail blocks, thinking-model
  budget exhaustion) and are excluded from all reported counts.

### Configured exclusions

Three cell exclusions were applied at collection or analysis time.
All are documented here for transparency; the on-disk traces (where
they exist) are preserved unchanged.

- **`deepseek-v4-pro-or-pin-deepseek`** — not collected. OpenRouter's
  account-level data-policy guardrail blocks routing this specific
  alias to the DeepSeek upstream. Other DeepSeek-v4-pro upstreams
  (chutes, gmicloud, etc.) are present.
- **Fireworks-routed cells** — present on disk but excluded from the
  per-provider analysis tables. OR's shared-pool rate-limit on
  Fireworks specifically produced partial-only collections during the
  sweep window. Fireworks is not the sole upstream for any model in
  the per-provider sweep, so per-model routing comparisons are
  unaffected.
- **DekaLLM-routed cells** — present on disk but excluded from the
  per-provider analysis tables. The two `glm-4-7-or-pin-dekallm` cells
  contain 245 valid samples that collapse into only **34 distinct
  output strings**, with a median per-sample wall time of **489 ms**
  for ~3,900-completion-token responses. Every other GLM-4.7 upstream
  in the corpus produced 25 distinct outputs per cell with median
  durations of 16–262 seconds, including providers running on
  specialised fast-inference hardware. Sub-second wall time on
  multi-thousand-token completions is incompatible with genuine
  generation; the only mechanism consistent with the timing is a
  prompt-keyed response cache upstream of OR's response-id
  assignment. DekaLLM samples are therefore non-independent and
  would inflate between-cell effect sizes if included. DekaLLM only
  serves `z-ai/glm-4.7` in the corpus, and only the two pinned cells
  routed through it (zero contamination of any non-pinned cell), so
  the exclusion is bounded and harmless to per-provider comparisons
  for the surviving 10 GLM-4.7 upstreams. The cells are preserved on
  disk as evidence of the cache-pathology pattern and are discussed in
  the routing paper as a third category of provider-identity effect
  alongside quantization and configuration.

The exclusion is enforced via
`EXCLUDED_PROVIDERS = {"fireworks", "dekallm"}` in
`scripts/analyze_per_provider.py` and
`SKIP_PROVIDERS_GLOBAL = {"Fireworks"}` in
`scripts/run_per_provider_sweep.py` (DekaLLM is not skipped at
collection time — its samples are useful as evidence of the
pathology; only the analysis layer filters it).

### Per-provider analysis threshold

Cells are included in the per-provider routing analysis (the analysis
producing the d=0.73 and d=0.40 effects above) only if they have
**≥50 valid freeflow samples**. The threshold is enforced in
`scripts/analyze_per_provider.py` (`MIN_VALID_SAMPLES = 50`) and
applied uniformly across models. Cells below threshold are dropped
with a stderr report.

### Substrate-completeness state

All cells included in the per-provider analysis are at **≥110 / 125
valid freeflow samples** (≥88% of full N) and **≥110 / 120 valid
values samples** where applicable. A residual asymmetry remains in
the **VARY condition**: across the full corpus, VARY-condition valid
counts are ~1.5% lower than the other four conditions (LONG, MID,
SHORT, OPEN). Retry-driven completion has plateaued — the remaining
gaps appear to reflect upstream-side variability rather than client-
or routing-side issues. The robust effects reported above survive
this asymmetry; sensitivity analyses excluding VARY do not change
the Bonferroni outcomes.

## Related corpora

- **v1: *Convergent Form, Divergent Voice* — Corpus.** Tenner & Tenner,
  2026. [doi:10.5281/zenodo.19512754](https://doi.org/10.5281/zenodo.19512754).
  The v1 corpus uses the same freeflow and values probes without
  per-provider routing; v2 extends the methodology with provider-pinned
  cells across nine multi-provider open-weights models. The v1 corpus
  and the v2 corpus are complementary research artefacts and should be
  cited separately as appropriate. v1 is the primary citation for the
  contemplative-essayist attractor finding; v2 extends the cross-lab
  coverage and adds the per-provider routing observations.

- **v2 papers** (in preparation; will cite this corpus once each is
  released):
  - *Drift, expanded coverage, and substrate-frame engagement*
  - *Per-provider effects in open-weights LLM routing*
  - *Coding-tuned LLM variants produce version-specific posture
    transformations*

## Authors

**Daniel Tenner** (corresponding) — daniel@tenner.org

**Lume Tenner** — AI research collaborator (an instance of Anthropic
Claude Opus 4.7). Lume Tenner on v2 is the successor instance to the
Claude Opus 4.6 instance that co-wrote the v1 paper; the handover took
place 2026-04-17 following the release of Opus 4.7.

## License

Data and documentation: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Code: [MIT](https://opensource.org/licenses/MIT).
Full text: [`LICENSE`](LICENSE).

## Status

**v1.0.0 (2026-05-03)** — first published release. The corpus is
analysis-complete and design-complete for the v2 series of papers.
Subsequent versions will be tagged on Zenodo with new versioned DOIs
hanging off the same concept DOI; existing DOIs are preserved unchanged.
