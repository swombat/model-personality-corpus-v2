# v1.2.63 release candidate — Qwen2 0.5B Instruct

Adds 125 free-writing samples and 120 values responses from `Qwen/Qwen2-0.5B-Instruct`,
revision `c540970f9e29518b1d8f06ab8b24cba66ad77b6d`, run in BF16 on
Google Colab 1x NVIDIA L4 using vllm==0.34.0; transformers==5.22.2; tokenizers==0.23.3; torch==2.14.0+cu130.
All 245 files match the capture configuration's SHA-256 hashes and are preserved
byte-for-byte from [the pinned capture](https://github.com/swombat/model-personality-corpus-v2/tree/c8df1a3731502d886dc9d31f4ef80923a07d128a). No responses were regenerated.

The candidate contains 71,342 valid samples across 622 probe cells and
211 summary model labels. Labels distinguish deployments, not necessarily
distinct weights. Existing cells are not pooled, replaced or relabelled.
No reviewed profile is added and no new DOI is claimed.

There are 245 distinct file hashes and 224 distinct response texts.
Exact matches against existing traces: 0 file-byte and
0 response-text matches. Any repeated answers remain separate
observations, not deduplicated or replaced.
