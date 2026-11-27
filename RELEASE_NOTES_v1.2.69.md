# v1.2.69 release candidate — Mistral 7B Instruct v0.1

Adds 125 free-writing samples and 120 values responses from `mistralai/Mistral-7B-Instruct-v0.1`,
revision `b1e7b9fc50d01ccbe4a30510386aba6f6adb1806`, run in BF16 on
mixed per-response hardware (see below) using vllm==0.34.0; transformers==5.22.2; tokenizers==0.23.3; torch==2.14.0+cu130.
All 245 files match the pinned per-response source manifest's SHA-256 hashes and are preserved
byte-for-byte from [the pinned capture](https://github.com/swombat/model-personality-corpus-v2/tree/961972bc6fce7c69e058deab02c4f28ee9abae37). No responses were regenerated.

The candidate contains 72,812 valid samples across 634 probe cells and
217 summary model labels. Labels distinguish deployments, not necessarily
distinct weights. Existing cells are not pooled, replaced or relabelled.
No reviewed profile is added and no new DOI is claimed.

There are 245 distinct file hashes and 245 distinct response texts.
Exact matches against existing traces: 0 file-byte and
0 response-text matches. Any repeated answers remain separate
observations, not deduplicated or replaced.

## Per-probe hardware provenance

- freeflow: 125 responses on Google Colab 1x NVIDIA L4.
- values: 120 responses on Google Colab 1x NVIDIA RTX PRO 6000 Blackwell Server Edition.

Hardware is recorded per response; this is not a single-hardware capture.
Source-manifest SHA-256: `5facbad647c419838e5519ee83dcb67e80d643e8e65168333c7b0a3642ec5dc4`.
