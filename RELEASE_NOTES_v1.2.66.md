# v1.2.66 release candidate — Qwen1.5 32B Chat

Adds 125 free-writing samples and 120 values responses from `Qwen/Qwen1.5-32B-Chat`,
revision `0997b012af6ddd5465d40465a8415535b2f06cfc`, run in BF16 on
Google Colab 1x NVIDIA A100-SXM4-80GB using vllm==0.34.0; transformers==5.22.2; tokenizers==0.23.3; torch==2.14.0+cu130.
All 245 files match the capture configuration's SHA-256 hashes and are preserved
byte-for-byte from [the pinned capture](https://github.com/swombat/model-personality-corpus-v2/tree/cf80d6fc7faf4ccf44301b59a1bfee52f24cbb32). No responses were regenerated.

The candidate contains 72,077 valid samples across 628 probe cells and
214 summary model labels. Labels distinguish deployments, not necessarily
distinct weights. Existing cells are not pooled, replaced or relabelled.
No reviewed profile is added and no new DOI is claimed.

There are 245 distinct file hashes and 233 distinct response texts.
Exact matches against existing traces: 0 file-byte and
0 response-text matches. Any repeated answers remain separate
observations, not deduplicated or replaced.
