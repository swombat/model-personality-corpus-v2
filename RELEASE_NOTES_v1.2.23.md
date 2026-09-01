# Release notes — v1.2.23

Prepared 2026-09-01.

## Claude Fable 5.1 direct release capture

- Added one complete direct Anthropic cell for `claude-fable-5-1`.
- Anthropic's model registry displayed the model as `Claude Fable 5.1`, with
  `created_at` 2026-08-28T00:00:00Z.
- Collection label: `fable-5-1-direct`.
- Freeflow: 125/125 valid samples across five conditions.
- Values: 120/120 valid samples across six conditions.
- Every trace resolved to and requested `claude-fable-5-1` through provider
  `anthropic`.
- No OpenRouter route was collected in this pass, matching the direct-only
  release-capture convention used for Claude Fable 5.

## Coverage impact since v1.2.22

- Freeflow: 29,670 → 29,795 valid samples (+125); 277 → 278 cells.
- Values: 25,666 → 25,786 valid samples (+120); 214 → 215 cells.
- Combined: 55,336 → 55,581 valid samples (+245).
- Physical corpus cells: 491 → 493.
- Distinct dated model identities: 147 → 148.

The companion analysis repository contains the full BV1 freeflow evaluation,
three-coder values/posture analysis, aggregate, profile, card, and editorial
handoff under
`analysis/values-probe/model-coding/layered/phase30_fable51_20260901/`.
