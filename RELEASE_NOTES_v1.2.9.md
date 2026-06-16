# Release notes — v1.2.9

Prepared: 2026-06-16

## Added

- OpenAI open-weight model cells via OpenRouter pinned to Amazon Bedrock only:
  - `gpt-oss-120b-or-pin-amazon-bedrock`
  - `gpt-oss-20b-or-pin-amazon-bedrock`
- OpenAI direct GPT-5 small-tier cells:
  - `gpt-5-mini-direct`
  - `gpt-5-nano-direct`

Each added cell has complete Corpus V2 coverage: 125 freeflow samples and 120 values-probe samples.

## Collection safety notes

- `gpt-oss-*` collection is pinned to OpenRouter provider `Amazon Bedrock` with fallbacks disabled.
- DekaLLM and Google were intentionally not used for these cells because of caching/suspicion concerns.
- Monitor/top-up scripts preserve valid samples, retry missing/error-like outputs, and check for `thinking budget exceeded`/rate-limit/upstream-error style failures.

## Regenerated

- `data/CORPUS_SUMMARY.md`
- `tables/summary.md`
- `tables/cells.tsv`
