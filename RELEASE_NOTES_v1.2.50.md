# v1.2.50 — Qwen2.5-32B-Instruct Colab raw release candidate

2026-11-25. Adds 245 revision-pinned raw samples: 125 freeflow (25 each
LONG/MID/SHORT/OPEN/VARY) and 120 values (10 each CTRL1/CTRL2/CTRL3,
30 each G1/G2/G3). Cell: `qwen2-5-32b-instruct-colab-vllm-bf16-r5ede1c97`.

Model `Qwen/Qwen2.5-32B-Instruct`, revision
`5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd`, BF16, served with vLLM 0.34.0
on one Google Colab NVIDIA A100-SXM4-80GB. This is an additional deployment
of existing weights, not a new model release. Full recorded runtime and
import scope: [provenance](notes/qwen2-5-32b-instruct-colab-2026-11-25/README.md).

## Import and interventions

The 245 traces are byte-identical to source commit
`c52ad1321b2fa3cc91fdc5972ba6b2131b0cf0b2`. No raw response editing,
recapture, or analysis changes were performed for this candidate.
No unrelated source-branch changes were imported.

## Counts

Regenerated summary: 68,157 valid samples across 596 probe cells and
198 summary model labels (freeflow 36,251 / 330 cells; values 31,906 /
266 cells). The existing summary treats the Colab suffix as a separate
model label from historical Qwen2.5-32B deployments; the model total is
not a unique-weight count. Historical QA is not re-certified by these totals.

## Verification and publication status

Verified exact source blobs, expected sample IDs/counts, JSON parsing,
non-empty results, model/revision/BF16/runtime/hardware provenance and
completion finish reasons across all imported samples. Corpus summary
regenerated; citation and Zenodo metadata updated.

Local release candidate only: no push, tag, deployment, GitHub release,
Zenodo upload, new DOI, companion analysis release, or API spend claim.
