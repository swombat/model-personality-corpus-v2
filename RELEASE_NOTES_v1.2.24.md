# Release notes — v1.2.24

Prepared 2026-09-04.

## GPT-6 Astra direct release capture

- Added one complete direct OpenAI cell for `gpt-6-astra`.
- The configured account's model registry exposed the exact id
  `gpt-6-astra`, with registry `created` timestamp
  2026-08-27T18:00:04Z.
- A live Responses API smoke test succeeded before collection.
- Collection label: `gpt-6-astra-direct`.
- Freeflow: 125/125 valid samples across five conditions.
- Values: 120/120 valid samples across six conditions.
- Every trace resolved to and requested `gpt-6-astra` through provider
  `openai`.
- The direct collector now routes GPT-6 models through the Responses API.
- No OpenRouter route was collected in this pass.

## Coverage impact since v1.2.23

- Freeflow: 29,795 → 29,920 valid samples (+125); 278 → 279 cells.
- Values: 25,786 → 25,906 valid samples (+120); 215 → 216 cells.
- Combined: 55,581 → 55,826 valid samples (+245).
- Physical corpus cells: 493 → 495.
- Distinct dated model identities: 148 → 149.

The companion analysis repository contains the full BV1 freeflow evaluation,
three-coder values/posture analysis, aggregate, profile, card, and editorial
handoff under
`analysis/values-probe/model-coding/layered/phase33_gpt6_astra_20260904/`.
