# v1.2.48 — OpenAI GPT-6.2 Astra and GPT-6.2 Sol

2026-11-17. Adds 490 verified raw samples: for each model, 125 freeflow (25 per
condition) and 120 values. Cells: `gpt-6-2-astra-or-pin-openai` and
`gpt-6-2-sol-or-pin-openai`. Requested models: `openai/gpt-6.2-astra` ($8 / $40
per M) and `openai/gpt-6.2-sol` ($2 / $10), each pinned to **OpenAI** through
OpenRouter (endpoints `-20261117`), with no fallbacks and no service tier
requested (standard, not "fast"). Reasoning and sampling are the provider's
defaults (medium reasoning). Prompts and technical retry budgets are
unchanged. The `-pro` SKUs are the same models in max-thinking mode and are
skipped. Runs `20261117-gpt-6-2-astra-house` and `20261117-gpt-6-2-sol-house`
were collected on release day by Lume from the souls.house container, on
Daniel's ask (souls.house YAqvNY).

The release date, 2026-11-17, comes from OpenAI's GPT-6.2 System Card at
https://deploymentsafety.openai.com/gpt-6-2-astra-sol ("Published November 17,
2026"), which covers both models. It is saved as `announcement.html` in each
of `notes/gpt-6-2-astra-2026-11-17/` and `notes/gpt-6-2-sol-2026-11-17/`. The
openai.com announcement returned HTTP 403. The OpenRouter listing timestamp is
not used as release evidence.

## Interventions

None. Every trace is the model's first valid answer under the normal ladders.
Values splits were settled by the standard single independent adjudication
(Astra 2 initial, Sol 1; no residual splits).

## Counts

The regenerated corpus summary reports 67,667 valid samples across 592 cells
and 196 distinct models (freeflow 36,001 / 328 cells; values 31,666 / 264
cells). These summary counts are not a claim that all historical samples
passed this run's QA.

Raw capture cost, counted once per trace (`upstream_inference_cost`, BYOK,
billed to the OpenAI key; OpenRouter reported `cost` 0): GPT-6.2 Astra $5.95
(148k completion tokens, 1.4k reasoning), GPT-6.2 Sol $1.98 (197k completion,
30.6k reasoning).

Companion analysis: v1.4.47.
