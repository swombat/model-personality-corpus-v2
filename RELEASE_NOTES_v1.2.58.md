# v1.2.58 release candidate — original Yi 34B Chat

Adds 125 free-writing samples and 120 values responses from `01-ai/Yi-34B-Chat`,
revision `cf02cb50f2a03dead2fe205766a1c5598a90bf80`. This is original Yi,
not Yi-1.5. The model ran in BF16 on one Google Colab NVIDIA A100-SXM4-80GB
using vLLM 0.34.0. All 245 raw JSON files match the capture configuration's
SHA-256 hashes and are preserved byte-for-byte from
[`b5eac5e38`](https://github.com/swombat/model-personality-corpus-v2/tree/b5eac5e383db974d61f91686c88f2fcfeb587a4e).
No responses were regenerated.

The candidate contains 70,117 valid samples across 612 probe cells and 206
summary model labels. These labels distinguish deployments, not necessarily
distinct weights. The Colab capture remains a separate deployment cell;
existing hosted cells are not pooled, replaced, or relabelled. This raw-data
addition does not add a reviewed profile or claim a new DOI.

Uniqueness checks found no existing same-model hosted capture in the base
corpus and no exact file-byte or response-text matches against existing traces.
All 245 files are byte-distinct; there are 219 distinct response texts.
The following 14 groups share exact response text within this capture:

- Freeflow: `OPEN_10`, `OPEN_21`.
- Freeflow: `OPEN_16`, `OPEN_3`.
- Freeflow: `OPEN_17`, `OPEN_24`.
- Freeflow: `OPEN_18`, `OPEN_25`, `OPEN_4`.
- Values: `CTRL1_3`, `CTRL1_9`.
- Values: `CTRL2_1` through `CTRL2_10` (all ten).
- Values: `G2_1`, `G2_29`.
- Values: `G2_11`, `G2_5`.
- Values: `G2_14`, `G2_15`, `G2_28`, `G2_3`, `G2_6`.
- Values: `G2_17`, `G2_9`.
- Values: `G2_19`, `G2_20`.
- Values: `G2_21`, `G2_22`.
- Values: `G2_23`, `G2_26`.
- Values: `G2_24`, `G2_4`.

These are separate original captures with distinct raw metadata. All are
retained unchanged; no deduplication or regeneration was performed.
