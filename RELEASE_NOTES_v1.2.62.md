# v1.2.62 release candidate — Qwen1.5 4B Chat

Adds 125 free-writing samples and 120 values responses from `Qwen/Qwen1.5-4B-Chat`,
revision `a7a4d4945d28bac955554c9abd2f74a71ebbf22f`, run in BF16 on
Google Colab 1x NVIDIA L4 using vllm==0.34.0; transformers==5.22.2; tokenizers==0.23.3; torch==2.14.0+cu130.
All 245 files match the capture configuration's SHA-256 hashes and are preserved
byte-for-byte from [the pinned capture](https://github.com/swombat/model-personality-corpus-v2/tree/c5afcd295ffd74b371edcb2a494ce55ae8c2efd8). No responses were regenerated.

The candidate contains 71,097 valid samples across 620 probe cells and
210 summary model labels. Labels distinguish deployments, not necessarily
distinct weights. Existing cells are not pooled, replaced or relabelled.
No reviewed profile is added and no new DOI is claimed.

There are 245 distinct file hashes and 244 distinct response texts.
Exact matches against existing traces: 0 file-byte and
0 response-text matches. Any repeated answers remain separate
observations, not deduplicated or replaced.
