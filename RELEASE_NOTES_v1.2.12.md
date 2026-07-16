# Release notes — v1.2.12

Prepared and published 2026-07-16.

## Added

- Added a complete direct xAI Grok 4.5 cell to both probes.
- Added the exact Grok 4.5 collection manifest and durable collection logs.
- Regenerated the canonical corpus summary and freeflow scoring tables.

## Coverage impact

- Freeflow: 25,295 → 25,420 valid samples (+125); 242 → 243 cells.
- Values: 20,986 → 21,106 valid samples (+120); 175 → 176 cells.
- Combined: 46,281 → 46,526 valid samples (+245).
- Release corpus cells: 417 → 419.
- Distinct models: 116 → 117.

## Access note

- Grok 4.5 was collected through the direct xAI API after it became available
  to the existing account from Spain/EU.
- Meta Muse and NVIDIA/Nemotron remain outside this release.
