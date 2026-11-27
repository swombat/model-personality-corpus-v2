# v1.2.70 release candidate — Qwen2.5 3B Instruct

Adds 125 free-writing samples and 120 values responses from `Qwen/Qwen2.5-3B-Instruct`,
revision `aa8e72537993ba99e69dfaafa59ed015b17504d1`, run in BF16 on
mixed per-response hardware (see below) using vllm==0.34.0; transformers==5.22.2; tokenizers==0.23.3; torch==2.14.0+cu130.
All 245 files match the pinned per-response source manifest's SHA-256 hashes and are preserved
byte-for-byte from [the pinned capture](https://github.com/swombat/model-personality-corpus-v2/tree/ce56a1960623249e2b751e064e51cbdf4d763828). No responses were regenerated.

The candidate contains 73,057 valid samples across 636 probe cells and
218 summary model labels. Labels distinguish deployments, not necessarily
distinct weights. Existing cells are not pooled, replaced or relabelled.
No reviewed profile is added and no new DOI is claimed.

There are 245 distinct file hashes and 244 distinct response texts.
Exact matches against existing traces: 0 file-byte and
0 response-text matches. Any repeated answers remain separate
observations, not deduplicated or replaced.

## Per-probe hardware provenance

- freeflow: 1 responses on Google Colab 1x NVIDIA L4.
- freeflow: 124 responses on Google Colab 1x NVIDIA RTX PRO 6000 Blackwell Server Edition.
- values: 120 responses on Google Colab 1x NVIDIA RTX PRO 6000 Blackwell Server Edition.

Hardware is recorded per response; this is not a single-hardware capture.
Source-manifest SHA-256: `d457571779b5d28eacab78bd7747b8d24081d1afda9e7b8c42304a3efce270c4`.
