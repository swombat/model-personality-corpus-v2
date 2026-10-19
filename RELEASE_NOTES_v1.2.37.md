# v1.2.37 — DeepSeek V4.1 Flash 1017

2026-10-19. Adds 245 verified raw samples: 125 freeflow (25 per condition)
and 120 values, `deepseek-v4-1-flash-1017-or-pin-deepseek`. Requested model:
`deepseek/deepseek-v4.1-flash-1017`, pinned to **DeepSeek** through
OpenRouter, no fallbacks. Reasoning and sampling are the provider's defaults;
prompts, token ladders and technical retry budgets are unchanged. Run
`20261018-deepseek-v4-1-flash-1017-house`, collected the day after release by
Lume from the souls.house container.

A new snapshot of V4.1 Flash with its own weights (Hugging Face
`deepseek-ai/DeepSeek-V4.1-Flash-1017`), not a serving or reasoning SKU, so it
gets its own cell, like V4 Flash 0731 and V4 Pro 0813.

Release date 2026-10-17 comes from DeepSeek's API Docs news post
"DeepSeek-V4.1-Flash-1017 Release" (https://api-docs.deepseek.com/news/news261017).
It is saved with the endpoint snapshot in
`notes/deepseek-v4-1-flash-1017-2026-10-17/`. The OpenRouter listing timestamp
is not used as release evidence.

## Interventions

None: all 245 capture tasks completed within their normal attempt budgets,
and the analysis side needed no repairs or evaluator variants either.

## Counts

The regenerated corpus summary reports 64,482 valid samples across 566 cells
and 183 distinct models (freeflow 34,376 / 315 cells; values 30,106 / 251
cells). These summary counts are not a claim that all historical samples
passed this run's QA.

Raw capture cost, summed from the per-call costs in the traces: $0.20
(327k completion tokens, 157k of them reasoning).

Companion analysis: v1.4.31.
