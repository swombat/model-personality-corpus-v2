# Release notes — v1.2.11

Prepared and published 2026-07-14.

## Added

- Added 33 complete model cells to both probes:
  - 7 OpenAI direct models: GPT-5.6 Sol, Terra, and Luna; GPT-5.4 mini and
    nano; GPT-5.1 Codex Max and Codex Mini.
  - 2 xAI direct models: Grok 4.20 0309 reasoning and non-reasoning modes.
  - 16 Mistral-family models, including Devstral 2512, Codestral 2508,
    Mistral Large/Medium/Small releases, Ministral 3B/8B/14B, Nemo, Saba,
    and Mixtral 8x22B.
  - 8 Llama models spanning Llama 3.1, 3.2, 3.3, and Llama 4 Scout/Maverick.
- Added the exact collection manifest used for the 2026-07-14 sweep.
- Regenerated the canonical corpus summary and freeflow scoring tables.

## Coverage impact

- Freeflow: 21,170 → 25,295 valid samples (+4,125); 209 → 242 cells.
- Values: 17,026 → 20,986 valid samples (+3,960); 142 → 175 cells.
- Combined: 38,196 → 46,281 valid samples (+8,085).
- Release corpus cells: 351 → 417.
- Distinct models: 83 → 116.

## Route and exclusion notes

- OpenAI models were collected through the direct OpenAI API only.
- OpenAI Pro variants were excluded for cost.
- Open-weights OpenRouter routes were pinned to named upstream providers with
  fallbacks disabled.
- Grok 4.5, Meta Muse, and NVIDIA/Nemotron are not part of this release.
