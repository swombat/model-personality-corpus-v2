# Release notes — v1.2.14

Prepared 2026-07-22 from collection completed 2026-07-21.

## Added

- Added complete OpenRouter cells for:
  - `google/gemini-3.6-flash`, pinned to Google.
  - `google/gemini-3.5-flash-lite`, pinned to Google.
  - `thinkingmachines/inkling`, pinned to Together.
- Added the exact collection manifest, smoke records, and restartable
  collection logs.
- Regenerated the canonical corpus summary and freeflow scoring tables.

## Coverage impact

- Freeflow: 25,545 → 25,920 valid samples (+375); 244 → 247 cells.
- Values: 21,226 → 21,586 valid samples (+360); 177 → 180 cells.
- Combined: 46,771 → 47,506 valid samples (+735).
- Release corpus cells: 421 → 427.
- Distinct models: 118 → 121.

## Route provenance

- All 245 Gemini 3.6 Flash traces resolved to
  `google/gemini-3.6-flash` on the Google upstream.
- All 245 Gemini 3.5 Flash-Lite traces resolved to
  `google/gemini-3.5-flash-lite` on the Google upstream.
- All 245 Inkling traces resolved to `thinkingmachines/inkling` on the
  Together upstream.
