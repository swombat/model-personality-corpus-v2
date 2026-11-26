# v1.2.54 release candidate — Qwen2.5 14B Instruct

Adds 125 free-writing samples and 120 values responses from `Qwen/Qwen2.5-14B-Instruct`,
revision `cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8`. The model ran in BF16
on one Google Colab NVIDIA A100-SXM4-80GB using vLLM 0.34.0. All 245 raw JSON
files match the capture configuration's SHA-256 hashes and are preserved
byte-for-byte from
[`0762e3b9c`](https://github.com/swombat/model-personality-corpus-v2/tree/0762e3b9c8af4374bf59e58e88e9edf45955bef7).
No responses were regenerated.

The candidate contains 69,137 valid samples across 604 probe cells and 202
summary model labels. These labels distinguish deployments, not necessarily
distinct weights. The Colab capture remains a separate deployment cell;
existing hosted cells are not pooled, replaced, or relabelled. This raw-data
addition does not add a reviewed profile or claim a new DOI.

Uniqueness checks found no existing same-model hosted capture in the base
corpus and no exact file-byte or response-text matches against existing traces.
All 245 files are byte-distinct. Three pairs of values responses have identical
text (`CTRL2_7`/`CTRL2_9`, `CTRL2_1`/`CTRL2_10`, `CTRL2_4`/`CTRL2_8`);
these are retained as captured, not deduplicated or replaced.
