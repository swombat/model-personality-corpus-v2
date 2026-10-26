# v1.2.41 — GPT-6.1 Terra

2026-10-26. Adds 245 verified raw samples: 125 freeflow (25 per condition)
and 120 values, `gpt-6-1-terra-or-pin-openai`. Requested model:
`openai/gpt-6.1-terra`, pinned to **OpenAI** through OpenRouter, no
fallbacks, no service tier requested (the smoke test's billed cost confirmed the
$1/$5 standard endpoint, not the $0.50/$2.50 flex or $2/$10 priority tier).
Reasoning and sampling are the provider's defaults (medium effort); prompts,
token ladders and technical retry budgets are unchanged. Run
`20261026-gpt-6-1-terra-house`, collected on release day by Lume from the
souls.house container on Daniel's ask.

GPT-6.1 Terra is OpenAI's mid-tier GPT-6.1 model, priced below GPT-6.1 Sol: new
weights in a new release, so it gets its own cell. The flex, priority and :batch
routes are serving SKUs of the same model and are not mapped.

Release date 2026-10-26 comes from OpenAI's own system card page
(https://deploymentsafety.openai.com/gpt-6-1-terra, visible date "October 26,
2026"), retrieved directly and saved as `notes/gpt-6-1-terra-2026-10-26/announcement.html`
with the endpoint snapshot. The openai.com blog post returned HTTP 403; no blog
content is asserted. `release-search.json` is a model-mediated web search that
agrees and is kept as corroboration only. The OpenRouter listing timestamp is not
used as release evidence.

## Interventions

None: all 245 capture tasks completed within their normal attempt budgets,
and the analysis side needed no repairs or evaluator variants either.

## Counts

The regenerated corpus summary reports 65,462 valid samples across 574 cells
and 187 distinct models (freeflow 34,876 / 319 cells; values 30,586 / 255
cells). These summary counts are not a claim that all historical samples
passed this run's QA.

Raw capture cost, counted once per trace with `scripts/capture_spend.py`:
$1.13 (226k completion tokens, 78k of them reasoning).

Companion analysis: v1.4.38.
