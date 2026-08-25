# Release notes — v1.2.20

Prepared 2026-08-25.

## Dated Ox Alpha repeat

- Added a second complete paired capture of OpenRouter's anonymous
  `stealth/ox-alpha` model, collected on 2026-08-25.
- Preserved the prior 2026-08-21 capture as the distinct analytical identity
  `ox-alpha-260821`; the new capture is `ox-alpha-260825`.
- Collection was pinned to the sole listed `Stealth` upstream with fallbacks
  disabled.
- Requested and returned model identifiers remained `stealth/ox-alpha`; the
  served provider remained `Stealth`.
- The developer identity remains intentionally unknown.
- New freeflow cell: 125/125 valid samples.
- New values cell: 120/120 valid samples.
- OpenRouter reported zero collection cost.

## Coverage impact since v1.2.19

- Freeflow: 29,295 → 29,420 valid samples (+125); 274 → 275 cells.
- Values: 24,826 → 24,946 valid samples (+120); 207 → 208 cells.
- Combined: 54,121 → 54,366 valid samples (+245).
- Physical corpus cells: 481 → 483.
- Distinct dated model identities: 144 → 145.

## Provenance

- Prior physical cells:
  `ox-alpha-or-pin-stealth-20260821`
- New physical cells:
  `ox-alpha-260825-or-pin-stealth`
- Exact new collection configuration:
  `collection-manifest-2026-08-25-ox-alpha.json`

The dated split is analytical, not a claim that the underlying developer or
architecture changed.
