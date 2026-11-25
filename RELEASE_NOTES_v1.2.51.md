# v1.2.51 — Gemma-2-9B-IT Colab raw release candidate

2026-11-26. Adds 245 revision-pinned raw samples: 125 freeflow (25 each
LONG/MID/SHORT/OPEN/VARY) and 120 values (10 each CTRL1/CTRL2/CTRL3,
30 each G1/G2/G3). Cell: `gemma-2-9b-it-colab-vllm-bf16-r11c9b309`.

Model `google/gemma-2-9b-it`, revision
`11c9b309abf73637e4b6f9a3fa1e92e615547819`, BF16, served with vLLM 0.34.0
on one Google Colab NVIDIA L4. This is an additional deployment of existing
weights, not a new model release.
See [provenance](notes/gemma-2-9b-it-colab-2026-11-26/README.md).

## Import and interventions

All 245 traces are byte-identical to source commit
`d7c3868fe9b398dbb93132fc40e96e0739a188df` and match the queue's recorded
source-adoption SHA256 hashes. No raw response editing, recapture, or analysis
changes were performed. No unrelated source-branch changes were imported.

## Counts

Regenerated summary: 68,402 valid samples across 598 probe cells and
199 summary model labels (freeflow 36,376 / 331 cells; values 32,026 /
267 cells). The existing summary retains Colab deployment suffixes as separate
model labels; this is not a unique-weight count. Historical QA is not
re-certified by these totals.

## Verification and publication status

Verified source Git blobs and adoption SHA256s, expected sample IDs/counts,
JSON parsing, non-empty results, model/revision/BF16/runtime/hardware provenance,
and `stop` finish reasons across all 245 imports. Corpus summary regenerated;
citation and Zenodo metadata updated following the Qwen v1.2.50 layout.

Local release candidate only: no push, tag, deployment, GitHub release,
Zenodo upload, new DOI, companion analysis release, or API spend claim.
