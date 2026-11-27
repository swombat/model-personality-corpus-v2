# v1.2.64 release candidate — Mistral 7B Instruct v0.3

Adds 125 free-writing samples and 120 values responses from `mistralai/Mistral-7B-Instruct-v0.3`,
revision `c170c708c41dac9275d15a8fff4eca08d52bab71`, run in BF16 on
Google Colab 1x NVIDIA L4 using vllm==0.34.0; transformers==5.22.2; tokenizers==0.23.3; torch==2.14.0+cu130.
All 245 files match the capture configuration's SHA-256 hashes and are preserved
byte-for-byte from [the pinned capture](https://github.com/swombat/model-personality-corpus-v2/tree/281fca67b5197a58c710e0e1399a06a1ca595bb3). No responses were regenerated.

The candidate contains 71,587 valid samples across 624 probe cells and
212 summary model labels. Labels distinguish deployments, not necessarily
distinct weights. Existing cells are not pooled, replaced or relabelled.
No reviewed profile is added and no new DOI is claimed.

There are 245 distinct file hashes and 245 distinct response texts.
Exact matches against existing traces: 0 file-byte and
0 response-text matches. Any repeated answers remain separate
observations, not deduplicated or replaced.
