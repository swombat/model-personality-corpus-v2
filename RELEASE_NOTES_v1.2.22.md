# Release notes — v1.2.22

Prepared 2026-08-27.

## GLM-5.3-Flash persona-prompt intervention ladder

- Added three complete 120-sample values cells for released
  `z-ai/glm-5.3-flash`, collected through OpenRouter with DeepInfra pinned and
  fallbacks disabled.
- The only experimental variable is the system prompt: P0 names the Ox Alpha
  persona; P1 adds plausible preview, provenance-secrecy and directness
  language; P2 adds an explicit openness instruction.
- These are intervention cells for the existing `glm-5-3-flash` identity, not
  new model identities.
- Exact protocol and prompts:
  `collection-manifest-2026-08-27-glm-5.3-flash-persona-ladder.json`.

## Coverage impact since v1.2.21

- Freeflow: unchanged at 29,670 valid samples across 277 cells.
- Values: 25,306 → 25,666 valid samples (+360); 211 → 214 cells.
- Combined: 54,976 → 55,336 valid samples.
- Physical corpus cells: 488 → 491.
- Distinct dated model identities: unchanged at 147.

## Provenance

- `glm-5-3-flash-or-pin-deepinfra-p0-20260827`
- `glm-5-3-flash-or-pin-deepinfra-p1-20260827`
- `glm-5-3-flash-or-pin-deepinfra-p2-20260827`

The canonical interpretation and three-coder posture analysis live in the
companion analysis repository under
`analysis/values-probe/model-coding/layered/phase29_glm53_flash_persona_ladder/`.
