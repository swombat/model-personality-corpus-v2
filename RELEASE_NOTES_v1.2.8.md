# Release notes — v1.2.8

Prepared: 2026-06-16

## Added

- Legacy OpenAI OpenRouter cells: `gpt-3-5-turbo-or`, `gpt-4-or`, `gpt-4-turbo-or`.
- OpenAI mini/nano OpenRouter cells: `gpt-4o-mini-or`, `gpt-4-1-mini-or`, `gpt-4-1-nano-or`.
- Z.ai direct GLM cell: `glm-5-2-direct`.

Each added cell has complete Corpus V2 coverage: 125 freeflow samples and 120 values-probe samples.

## Harness notes

- `zai-direct` disables thinking for GLM-5.x corpus collection so traces capture final responses rather than reasoning scratchpad.
- Legacy OpenAI OpenRouter collection used conservative output-token settings to avoid invalid legacy settings.

## Regenerated

- `data/CORPUS_SUMMARY.md`
- `tables/summary.md`
- `tables/cells.tsv`
