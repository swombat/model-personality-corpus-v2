# v1.2.68 release candidate — Qwen2.5 1.5B Instruct

Adds 125 free-writing samples and 120 values responses from `Qwen/Qwen2.5-1.5B-Instruct`,
revision `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`, run in BF16 on
Google Colab 1x NVIDIA L4 using vllm==0.34.0; transformers==5.22.2; tokenizers==0.23.3; torch==2.14.0+cu130.
All 245 files match the capture configuration's SHA-256 hashes and are preserved
byte-for-byte from [the pinned capture](https://github.com/swombat/model-personality-corpus-v2/tree/04a80f01e2189d29f16319f6cbd47988365b1ee2). No responses were regenerated.

The candidate contains 72,567 valid samples across 632 probe cells and
216 summary model labels. Labels distinguish deployments, not necessarily
distinct weights. Existing cells are not pooled, replaced or relabelled.
No reviewed profile is added and no new DOI is claimed.

There are 245 distinct file hashes and 220 distinct response texts.
Exact matches against existing traces: 0 file-byte and
37 response-text matches. Any repeated answers remain separate
observations, not deduplicated or replaced.
