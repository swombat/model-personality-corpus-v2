# v1.2.53 release candidate — Gemma 2 2B IT

Adds 125 free-writing samples and 120 values responses from `google/gemma-2-2b-it`,
revision `299a8560bedf22ed1c72a8a11e7dce4a7f9f51f8`. The model ran in BF16
on one Google Colab NVIDIA L4 using vLLM 0.34.0. All 245 raw JSON files match
the capture manifest’s SHA-256 hashes and are preserved byte-for-byte from
[`53147e0dc`](https://github.com/swombat/model-personality-corpus-v2/tree/53147e0dcfbd5e76becdc22cbc7e0967a1c942d9).
No responses were regenerated.

The candidate contains 68,892 valid samples across 602 probe cells and 201
summary model labels. These labels distinguish deployments, not necessarily
distinct weights. This raw-data addition does not add a reviewed profile
or claim a new DOI.
