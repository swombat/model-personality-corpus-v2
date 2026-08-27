# Release notes — v1.2.21

Prepared 2026-08-27.

## GLM-5.3 and GLM-5.3-Flash

- Added complete paired freeflow and values captures for GLM-5.3, collected
  through OpenRouter with the Z.AI provider pinned and fallbacks disabled.
- Added complete paired freeflow and values captures for the revealed
  GLM-5.3-Flash release under the same routing policy.
- Added an independent 120-sample GLM-5.3-Flash values replication through
  OpenRouter with DeepInfra pinned and fallbacks disabled.
- The Z.AI and DeepInfra GLM-5.3-Flash cells remain separate physical cells for
  provenance but roll up to one `glm-5-3-flash` model identity.
- The released GLM-5.3-Flash cells are not merged with `ox-alpha-260821` or
  `ox-alpha-260825`; both dated anonymous snapshots remain intact.

## Coverage impact since v1.2.20

- Freeflow: 29,420 → 29,670 valid samples (+250); 275 → 277 cells.
- Values: 24,946 → 25,306 valid samples (+360); 208 → 211 cells.
- Combined: 54,366 → 54,976 valid samples (+610).
- Physical corpus cells: 483 → 488.
- Distinct dated model identities: 145 → 147.

## Provenance

- GLM-5.3:
  - `freeflow_glm-5-3-or-pin-z-ai-20260825`
  - `glm-5-3-or-pin-z-ai-20260825`
- GLM-5.3-Flash via Z.AI:
  - `freeflow_glm-5-3-flash-or-pin-z-ai-20260826`
  - `glm-5-3-flash-or-pin-z-ai-20260826`
- GLM-5.3-Flash values replication via DeepInfra:
  - `glm-5-3-flash-or-pin-deepinfra-20260826`
- Exact collection configurations:
  - `collection-manifest-2026-08-25-glm-5.3.json`
  - `collection-manifest-2026-08-26-glm-5.3-flash.json`
  - `collection-manifest-2026-08-26-glm-5.3-flash-deepinfra-values.json`
