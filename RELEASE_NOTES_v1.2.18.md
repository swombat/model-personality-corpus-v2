# Release notes — v1.2.18

Prepared 2026-08-11.

## Historical local full-precision capture

- Added complete paired freeflow and values cells for the official
  `01-ai/Yi-6B-Chat` and `zai-org/chatglm2-6b` assistant checkpoints.
- Both checkpoints were pinned to exact Hugging Face revisions and run
  sequentially on an Apple M1 Max with 64 GiB unified memory.
- Yi used the official BF16 safetensors checkpoint through
  Transformers 5.14.1 / PyTorch 2.13.0 on MPS.
- ChatGLM2 used the official FP16 PyTorch shards through its compatible
  Transformers 4.27.1 custom-code runtime on MPS.
- Every trace records model revision, runtime and version, weight precision,
  hardware, endpoint, and stop-sequence provenance under `local_deployment`.
- No quantized, distilled, ablated, jailbroken, or community-finetuned model
  was substituted.

## Coverage impact

- Freeflow: 27,545 → 27,795 valid samples (+250); 260 → 262 cells.
- Values: 23,146 → 23,386 valid samples (+240); 193 → 195 cells.
- Combined: 50,691 → 51,181 valid samples (+490).
- Release corpus cells: 453 → 457.
- Distinct models: 132 → 134.

## Initial attractor scores

- Yi-6B-Chat: composite **8** (`out`).
- ChatGLM2-6B: composite **3** (`out`).

These are among the lowest-scoring complete historical cells in this release
and provide useful pre-2024 anchors for the temporal personality analysis.

## Excluded compatibility artifact

The 25-sample Yi MLX compatibility attempt is preserved under
`discarded/2026-08-09-local-runtime-smoke-tests/`. It was superseded by the
complete official-BF16 Transformers cell and is excluded from canonical counts.
