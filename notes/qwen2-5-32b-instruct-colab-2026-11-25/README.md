# Qwen2.5-32B-Instruct — Colab provenance

Imported byte-for-byte from raw repository commit
`c52ad1321b2fa3cc91fdc5972ba6b2131b0cf0b2` (Reed, 2026-11-25).
Only these two source directories were imported:

- `data/traces_freeflow/freeflow_qwen2-5-32b-instruct-colab-vllm-bf16-r5ede1c97/`: 125 samples.
- `data/traces_values/qwen2-5-32b-instruct-colab-vllm-bf16-r5ede1c97/`: 120 samples.

Each trace identifies `Qwen/Qwen2.5-32B-Instruct`, revision
`5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd`, bfloat16 weights,
Google Colab 1x NVIDIA A100-SXM4-80GB, and `vllm-openai (colab)`.
Recorded runtime: vLLM 0.34.0, transformers 5.22.2, tokenizers 0.23.3,
torch 2.14.0+cu130. The endpoint recorded in traces is loopback, not a public
service. No provider API route or API inference cost is claimed.

This is a deployment capture of existing weights, not evidence of a newly
released model. The date above is the import/capture date, not the model's
original release date. No raw responses were edited or rerun for this candidate.
Only raw traces are included: no analysis, adjudications, site assets, runtime
logs, credentials, or unrelated captures from the source branch.

The existing summary script does not strip the `-colab-vllm-bf16-r5ede1c97`
suffix. Consequently its 198 model labels include this deployment separately
from historical Qwen2.5-32B labels; this is not a claim of 198 unique weights.
