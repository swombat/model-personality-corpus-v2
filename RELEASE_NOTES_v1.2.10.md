# Release notes — v1.2.10

Prepared 2026-06-26; pending Zenodo deposit.

## Added

- Added OpenRouter freeflow route for GrokBuild: `grok-build-0-1-or`.
- OpenRouter model request: `x-ai/grok-build-0.1`; resolved model in traces: `x-ai/grok-build-0.1-20260520`.
- Complete freeflow coverage: 125/125 valid samples across LONG/MID/SHORT/OPEN/VARY.

## Coverage impact

- Freeflow: 20,795 → 20,920 valid samples (+125).
- Values: unchanged at 16,786 valid samples.
- Combined: 37,581 → 37,706 valid samples.
- Release corpus cells: 346 → 347.
- Distinct models: unchanged at 82.

## Notes

The direct xAI `grok-build-0-1-direct` cell remains the values-complete route for GrokBuild. This release adds route/provider comparison material for the freeflow substrate only.
