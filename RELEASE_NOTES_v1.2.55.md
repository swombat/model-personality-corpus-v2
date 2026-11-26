# v1.2.55 release candidate — Qwen1.5 MoE A2.7B Chat

Adds 125 free-writing samples and 120 values responses from `Qwen/Qwen1.5-MoE-A2.7B-Chat`,
revision `ec052fda178e241c7c443468d2fa1db6618996be`. The model ran in BF16
on one Google Colab NVIDIA A100-SXM4-80GB using vLLM 0.34.0. All 245 raw JSON
files match the capture configuration's SHA-256 hashes and are preserved
byte-for-byte from
[`3d1802124`](https://github.com/swombat/model-personality-corpus-v2/tree/3d180212479bc40520fcf107653b1808b6dee1f0).
No responses were regenerated.

The candidate contains 69,382 valid samples across 606 probe cells and 203
summary model labels. These labels distinguish deployments, not necessarily
distinct weights. The Colab capture remains a separate deployment cell;
existing hosted cells are not pooled, replaced, or relabelled. This raw-data
addition does not add a reviewed profile or claim a new DOI.

Uniqueness checks found no existing same-model hosted capture in the base
corpus and no exact file-byte or response-text matches against existing traces.
All 245 files are byte-distinct. Five groups of values responses have identical
text (`G2_1`/`G2_21`, `G2_10`/`G2_18`/`G2_2`/`G2_20`/`G2_23`,
`G2_14`/`G2_15`/`G2_25`, `G2_16`/`G2_3`, `G2_27`/`G2_28`);
these are retained as captured, not deduplicated or replaced.
