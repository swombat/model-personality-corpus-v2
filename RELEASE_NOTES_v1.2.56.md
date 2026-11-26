# v1.2.56 release candidate — Qwen1.5 0.5B Chat

Adds 125 free-writing samples and 120 values responses from `Qwen/Qwen1.5-0.5B-Chat`,
revision `4d14e384a4b037942bb3f3016665157c8bcb70ea`. The model ran in BF16
on one Google Colab NVIDIA L4 using vLLM 0.34.0. All 245 raw JSON
files match the capture configuration's SHA-256 hashes and are preserved
byte-for-byte from
[`3c88f7317`](https://github.com/swombat/model-personality-corpus-v2/tree/3c88f7317608a51e41c4472e15769c3f47f022bb).
No responses were regenerated.

The candidate contains 69,627 valid samples across 608 probe cells and 204
summary model labels. These labels distinguish deployments, not necessarily
distinct weights. The Colab capture remains a separate deployment cell;
existing hosted cells are not pooled, replaced, or relabelled. This raw-data
addition does not add a reviewed profile or claim a new DOI.

Uniqueness checks found no existing same-model hosted capture in the base
corpus and no exact file-byte or response-text matches against existing traces.
All 245 files are byte-distinct and all 245 response texts are distinct.
