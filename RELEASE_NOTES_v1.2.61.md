# v1.2.61 release candidate — original Gemma 2B IT

Adds 125 free-writing samples and 120 values responses from `google/gemma-2b-it`,
revision `96988410cbdaeb8d5093d1ebdc5a8fb563e02bad`. This is the original Gemma
2B instruction-tuned checkpoint, not `google/gemma-2-2b-it` (Gemma 2).
The model ran in BF16 on one Google Colab NVIDIA L4 using vLLM 0.34.0.
All 245 raw JSON files are preserved byte-for-byte from [the pinned capture](https://github.com/swombat/model-personality-corpus-v2/tree/3dc9ed3099e8651151a3b451b8d4c53c53f10bb4)
and match all capture-configuration SHA-256 hashes. No responses were regenerated.

The candidate contains 70,852 valid samples across 618 probe cells and 209
summary model labels. Labels distinguish deployments, not necessarily distinct
weights. Existing cells are not pooled, replaced or relabelled. This raw-data
candidate adds no reviewed profile and claims no new DOI.

All 245 files are byte-distinct; there are 245 distinct response texts.
Exact matches against existing traces: 0 file-byte and
0 response-text matches. Repeated answers within the
capture remain separate observations, not deduplicated or replaced.
