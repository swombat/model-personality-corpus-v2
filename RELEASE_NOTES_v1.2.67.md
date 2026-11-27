# v1.2.67 release candidate — Qwen2 1.5B Instruct

Adds 125 free-writing samples and 120 values responses from `Qwen/Qwen2-1.5B-Instruct`,
revision `2ebb13f1f55edeb5bd4b108d0ad589397a6ee4ac`, run in BF16 on
Google Colab 1x NVIDIA L4 using vllm==0.34.0; transformers==5.22.2; tokenizers==0.23.3; torch==2.14.0+cu130.
All 245 files match the capture configuration's SHA-256 hashes and are preserved
byte-for-byte from [the pinned capture](https://github.com/swombat/model-personality-corpus-v2/tree/8091986ac98e6af7877fb2eefd558882c9dba0f1). No responses were regenerated.

The candidate contains 72,322 valid samples across 630 probe cells and
215 summary model labels. Labels distinguish deployments, not necessarily
distinct weights. Existing cells are not pooled, replaced or relabelled.
No reviewed profile is added and no new DOI is claimed.

There are 245 distinct file hashes and 230 distinct response texts.
Exact matches against existing traces: 0 file-byte and
21 response-text matches. Any repeated answers remain separate
observations, not deduplicated or replaced.
