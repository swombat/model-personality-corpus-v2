# Release notes — v1.2.19

Prepared 2026-08-21.

## Ox Alpha anonymous-release capture

- Added complete paired freeflow and values cells for OpenRouter's anonymous
  `stealth/ox-alpha` model.
- Collection was pinned to the sole listed `Stealth` upstream with fallbacks
  disabled.
- The requested and returned model identifier remained
  `stealth/ox-alpha`; the served provider was recorded as `Stealth`.
- The lab identity remains intentionally unknown. No inferred developer label
  is written into corpus metadata.
- Freeflow: 125/125 valid samples.
- Values: 120/120 valid samples.
- OpenRouter reported zero collection cost.

## Included August expansion commits

This release also incorporates the already-collected Gemini 3.7 Flash cell and
Qwen 3.8 replicate cells added after v1.2.18.

## Coverage impact since v1.2.18

- Freeflow: 27,795 → 29,295 valid samples (+1,500); 262 → 274 cells.
- Values: 23,386 → 24,826 valid samples (+1,440); 195 → 207 cells.
- Combined: 51,181 → 54,121 valid samples (+2,940).
- Physical corpus cells: 457 → 481.
- Distinct models: 134 → 144.

## Ox Alpha provenance

Canonical cell: `ox-alpha-or-pin-stealth-20260821`

The exact collection configuration is preserved in
`collection-manifest-2026-08-21-ox-alpha.json`.
