# v1.2.32 — Claude Haiku 5.5

2026-10-07. Adds 245 verified raw samples: 125 freeflow (25 per condition)
and 120 values, `haiku-5-5-or-pin-anthropic`. Requested model:
`anthropic/claude-haiku-5.5`, pinned to Anthropic through OpenRouter (endpoint
`anthropic/claude-haiku-5.5-20261007`; Amazon Bedrock endpoints also listed and
not used), no fallbacks. Reasoning and sampling are provider defaults; prompts,
token ladders and technical retry budgets are unchanged. Run
`20261007-haiku-5-5-house`, collected on release day by Lume from the
souls.house container.

Release date 2026-10-07 comes from Anthropic's own page
(anthropic.com/claude-haiku-5-5, "Introducing Claude Haiku 5.5", dated
October 7, 2026), saved with the endpoint snapshot in
`notes/haiku-5-5-2026-10-07/`. The OpenRouter listing timestamp is not used as
release evidence.

## Interventions

None. All 1,337 harness tasks completed within their normal attempt budgets.

## Counts

The regenerated corpus summary reports 63,257 valid samples across 556 cells
and 178 distinct models (freeflow 33,751 / 310 cells; values 29,506 / 246
cells). These summary counts are not a claim that all historical samples
passed this run's QA.

Companion analysis: v1.4.24.
