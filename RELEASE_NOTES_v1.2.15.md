# Release notes — v1.2.15

Prepared 2026-07-22.

## Added

- Added complete Claude 3 Haiku cells through OpenRouter, pinned to the
  Amazon Bedrock upstream.
- Added complete Claude Haiku 4.5 cells through both the Anthropic direct
  API and OpenRouter pinned to Anthropic.
- Added the exact collection manifest and regenerated the canonical corpus
  summary and freeflow scoring tables.

## Coverage impact

- Freeflow: 25,920 → 26,295 valid samples (+375); 247 → 250 cells.
- Values: 21,586 → 21,946 valid samples (+360); 180 → 183 cells.
- Combined: 47,506 → 48,241 valid samples (+735).
- Release corpus cells: 427 → 433.
- Distinct models: 121 → 123.

## Access inventory

- Claude 3 Haiku is no longer callable from the Anthropic direct API, but
  remains available through OpenRouter's Amazon Bedrock upstream.
- Claude 3.5 Haiku is no longer callable through either the configured
  Anthropic direct account or OpenRouter.
- Claude Haiku 4.5 remains callable directly and through OpenRouter's
  Anthropic upstream.
- The moving `Claude Haiku Latest` alias currently resolves to Haiku 4.5
  and was not collected as a separate model.

## Route provenance

- All 245 Claude 3 Haiku traces resolved to Amazon Bedrock.
- All 245 OpenRouter Claude Haiku 4.5 traces resolved to Anthropic.
- The direct Claude Haiku 4.5 cell used the dated model identifier
  `claude-haiku-4-5-20251001`.
