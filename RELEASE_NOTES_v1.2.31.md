# v1.2.31 — Mistral Large 4

2026-10-07. Adds 245 verified raw samples: 125 freeflow (25 per condition)
and 120 values, `mistral-large-4-0-or-pin-mistral`. Requested model:
`mistralai/mistral-large-4-0`, pinned to Mistral through OpenRouter (endpoint
`mistral-large-4-0-20261006`, the only provider listed), no fallbacks.
Reasoning and sampling are provider defaults; prompts, token ladders and
technical retry budgets are unchanged. Run `20261006-mistral-large-4-house`,
collected by Lume from the souls.house container.

Release date 2026-10-06 comes from Mistral's announcement
(mistral.ai/news/mistral-large-4, schema.org datePublished 2026-10-06), saved
with the endpoint snapshot in `notes/mistral-large-4-0-2026-10-06/`. The
OpenRouter listing timestamp is not used as release evidence.

## Intervention

On launch day Mistral rate-limited for longer than the harness's six attempts
could absorb. 41 raw samples (24 freeflow, 17 values) exhausted their attempts
on HTTP 429. After the limit cleared, those 41 went through the harness's
repair lane: two further attempts each, original attempts and settings
untouched, and the repair logged as an intervention in the run record. All 41
succeeded on the first extra attempt. No other sample was retried beyond its
normal budget and no response was edited.

## Counts

The regenerated corpus summary reports 63,012 valid samples across 554 cells
and 177 distinct models (freeflow 33,626 / 309 cells; values 29,386 / 245
cells). These summary counts are not a claim that all historical samples
passed this run's QA.

Companion analysis: v1.4.23.
