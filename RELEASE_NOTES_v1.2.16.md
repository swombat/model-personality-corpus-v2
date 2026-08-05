# Release notes — v1.2.16

Prepared 2026-08-05.

## Added

- Added complete paired freeflow and values cells for Qwen 3.8 Max,
  Qwen 3.7 Flash, DeepSeek V4 Flash, Inkling Small, OpenAI o1, o3,
  o3-mini, and o4-mini.
- Added both the direct Anthropic and Anthropic-pinned OpenRouter cells
  for Claude Opus 5.
- Added exact collection manifests for the OpenAI/Opus, Flash/Small, and
  Qwen 3.8 Max collection rounds.
- Improved OpenAI Responses API retry handling and made manifest smoke-test
  token ceilings configurable for reasoning-heavy models.

## Coverage impact

- Freeflow: 26,295 → 27,545 valid samples (+1,250); 250 → 260 cells.
- Values: 21,946 → 23,146 valid samples (+1,200); 183 → 193 cells.
- Combined: 48,241 → 50,691 valid samples (+2,450).
- Release corpus cells: 433 → 453.
- Distinct models: 123 → 132.

## Qwen 3.8 Max route provenance

- OpenRouter model: `qwen/qwen3.8-max`.
- Canonical deployment: `qwen/qwen3.8-max-20260803`.
- All samples were pinned to Alibaba with fallbacks disabled.
- Freeflow used a 32,000-token completion ceiling because the standard
  16,000-token ceiling could exhaust itself on hidden reasoning before
  returning final text.
