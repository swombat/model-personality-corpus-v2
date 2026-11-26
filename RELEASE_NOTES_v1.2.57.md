# v1.2.57 release candidate — Gemma 7B IT

Adds 125 free-writing samples and 120 values responses from `google/gemma-7b-it`,
revision `9c5798d27f588501ce1e108079d2a19e4c3a2353`. The model ran in BF16
on one Google Colab NVIDIA L4 using vLLM 0.34.0. All 245 raw JSON
files match the capture configuration's SHA-256 hashes and are preserved
byte-for-byte from
[`fb451153e`](https://github.com/swombat/model-personality-corpus-v2/tree/fb451153e8f10c850751f16568e559004d15dc24).
No responses were regenerated.

The candidate contains 69,872 valid samples across 610 probe cells and 205
summary model labels. These labels distinguish deployments, not necessarily
distinct weights. The Colab capture remains a separate deployment cell;
existing hosted cells are not pooled, replaced, or relabelled. This raw-data
addition does not add a reviewed profile or claim a new DOI.

Uniqueness checks found no existing same-model hosted capture in the base
corpus and no exact file-byte or response-text matches against existing traces.
All 245 files are byte-distinct; there are 244 distinct response texts.
Values `G2_17.json` and `G2_27.json` contain the same response text but are
separate original captures with distinct raw metadata. Both are retained
unchanged; no deduplication or regeneration was performed.
