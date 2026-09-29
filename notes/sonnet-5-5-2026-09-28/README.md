# Claude Sonnet 5.5 — house capture provenance

Run `20260928-sonnet55-house`, 2026-09-28. Model ID
`anthropic/claude-sonnet-5.5`, pinned OpenRouter upstream `Anthropic`, fallbacks
disabled. New cell `sonnet-5-5-or-pin-anthropic`; analysis slug `sonnet-5-5`.

Endpoint metadata is preserved in `endpoints.json`. Advertised output maximum:
128,000 tokens. Frozen collection ladders: freeflow 16,000 → 32,768; values
4,000 → 8,000 → 16,000 → 32,768. Advance only on proven length truncation;
exhaustion escalates. These are heterogeneous technical caps, not a single
fixed-ceiling experiment. No explicit reasoning or sampling override.

Canonical target: 5 × 25 freeflow, 3 × 10 CTRL plus 3 × 30 G values.
The existing capture harness owns raw validation and bounded technical retries,
BV1, three content coders, consensus, three posture coders, consensus, one
initial-split adjudication, shared-values integration, synthesis and card-ready
validation. Disagreement is not a retry reason. Local protocol tests: 26 passed.
No old Mac backlog imported or restarted. Runtime state and private notification
transcripts are intentionally excluded from publication.

Release date 2026-09-28 is sourced to the official @claudeai announcement
self-thread, specifically https://x.com/claudeai/status/2104633140409192757
("Claude Sonnet 5.5 is available everywhere today"). Its parent introduction is
https://x.com/claudeai/status/2104633115620823187. Saved X helper outputs are
model-mediated retrievals, **not direct exported X records**; preserve that
provenance distinction. The OpenRouter listing timestamp was not substituted
for release evidence. The initially guessed Anthropic news URL returned 404
and was not used as a source.

This note records protocol and provenance, not completion or publication.
Completion requires all raw/analysis/integration gates, followed separately by
reviewed GitHub releases and verified Zenodo version records for both repos.
Website production deployment is a separate boundary.
