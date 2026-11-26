# v1.2.60 — Qwen1.5 14B Chat

Adds 125 free-writing and 120 values responses from `Qwen/Qwen1.5-14B-Chat`,
revision `9492b22871f43e975435455f5c616c77fe7a50ec`, run in BF16 on a
Colab A100. All 245 files match their recorded hashes at the
[capture commit](https://github.com/swombat/model-personality-corpus-v2/tree/6ebec5c07662040d91c4a5df53d2939e054c6e3d).
There are 242 distinct response texts; repeated answers remain separate
observations. The evaluator repair did not change any model response.

The corpus now contains 70,607 valid samples across 616 probe cells and
208 deployment labels. This release does not claim a new DOI.
