# Release notes — v1.2.13

Prepared and published 2026-07-16.

## Added

- Added a complete Kimi K3 cell through OpenRouter, pinned to the Moonshot AI
  upstream, to both probes.
- Added the exact Kimi K3 collection manifest and collection logs.
- Regenerated the canonical corpus summary and freeflow scoring tables.

## Coverage impact

- Freeflow: 25,420 → 25,545 valid samples (+125); 243 → 244 cells.
- Values: 21,106 → 21,226 valid samples (+120); 176 → 177 cells.
- Combined: 46,526 → 46,771 valid samples (+245).
- Release corpus cells: 419 → 421.
- Distinct models: 117 → 118.

## Direct-access note

- A direct collection through the existing Kimi coding endpoint reached the
  account's billing-cycle usage limit after 45 freeflow samples.
- That incomplete attempt is preserved under `discarded/` for provenance and
  is excluded from all release counts and analysis.
