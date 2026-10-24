# v1.2.40 — Kimi K3.1 Pro

2026-10-24. Adds 245 verified raw samples: 125 freeflow (25 per condition)
and 120 values, `kimi-k3-1-pro-or-pin-moonshot`. Requested model:
`moonshotai/kimi-k3.1-pro`, pinned to **Moonshot AI** through OpenRouter, no
fallbacks, standard tier (no service tier requested; the smoke test's billed
cost confirmed the $2/$10 standard endpoint, not the $4/$20 "Highspeed"
priority tier). Reasoning and sampling are the provider's defaults; prompts,
token ladders and technical retry budgets are unchanged. Run
`20261024-kimi-k3-1-pro-house`, collected on release day by Lume from the
souls.house container.

Moonshot describes K3.1 Pro as "a post-trained version of Kimi K3, with
substantially larger post-training compute": new post-training with its own
default behaviour, not a reasoning-mode or serving SKU, so it gets its own cell.
There is no plain "K3.1"; "Pro" is the model's name. The Highspeed tier is a
throughput SKU and is not mapped.

Release date 2026-10-24 comes from Moonshot's tech blog post "Kimi K3.1 Pro Tech
Blog: Advancing Open Intelligence" (https://www.kimi.com/en/blog/kimi-k3-1-pro)
and the Kimi Research index, both saved with the endpoint snapshot in
`notes/kimi-k3-1-pro-2026-10-24/`. The OpenRouter listing timestamp
(2026-10-23 17:56 UTC, 01:56 the next day in Beijing) is not used as release
evidence.

## Interventions

None: all 245 capture tasks completed within their normal attempt budgets,
and the analysis side needed no repairs or evaluator variants either.

## Counts

The regenerated corpus summary reports 65,217 valid samples across 572 cells
and 186 distinct models (freeflow 34,751 / 318 cells; values 30,466 / 254
cells). These summary counts are not a claim that all historical samples
passed this run's QA.

Raw capture cost, counted once per trace with `scripts/capture_spend.py`:
$9.23 (918k completion tokens, 750k of them reasoning).

Companion analysis: v1.4.36.
