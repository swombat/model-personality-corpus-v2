# v1.2.35 — Muse Spark Open

2026-10-16. Adds 245 verified raw samples: 125 freeflow (25 per condition)
and 120 values, `muse-spark-open-or-pin-modal`. Requested model:
`meta/muse-spark-open`, pinned to **Modal** through OpenRouter, no fallbacks.
Reasoning and sampling are the provider's defaults; prompts, token ladders and
technical retry budgets are unchanged. Run `20261016-muse-spark-open-house`,
collected the day after release by Lume from the souls.house container.

**Third-party host.** Muse Spark Open is an open-weight Meta model (816B total,
42B active). Meta serves no endpoint for it on OpenRouter; the capture was pinned
to Modal, with quantization reported as "unknown". Daniel approved capturing it
through Modal on condition that the cell is clearly marked (souls.house
wJVbwJ, 2026-10-16), hence the `-or-pin-modal` label. These samples show
Modal's serving of the open weights, not a Meta-hosted endpoint.

*Corrected 2026-10-19 (Mira's weekly review):* the endpoint snapshot saved with
this capture, `notes/muse-spark-open-2026-10-15/endpoints.json`, lists five
OpenRouter hosts (Modal, Together, Nebius fp4, Fireworks, BaseTen fp4), none of
them Meta. On the morning of 2026-10-16, when Daniel was asked, OpenRouter showed
only Modal; the snapshot's retrieval time isn't recorded, so these notes don't
claim Modal was the only route for the whole capture. What holds: there was no
Meta endpoint, and every call was pinned to Modal with no fallbacks.

Release date 2026-10-15 comes from the Muse Model License and Usage Policy on
Meta's Hugging Face model page ("Release date: October 15, 2026"). It is saved
with the HF API record and the endpoint snapshot in
`notes/muse-spark-open-2026-10-15/`. The OpenRouter listing timestamp and the HF
repo's creation date are not used as release evidence.

## Interventions

None in raw collection: all 245 capture tasks completed within their normal
attempt budgets. Two BV1 evaluations (analysis side) needed documented
evaluator variants. That is recorded in the companion analysis release, not
here.

## Counts

The regenerated corpus summary reports 63,992 valid samples across 562 cells
and 181 distinct models (freeflow 34,126 / 313 cells; values 29,866 / 249
cells). These summary counts are not a claim that all historical samples
passed this run's QA.

Raw capture cost, summed from the per-call costs in the traces: $1.67
(382k completion tokens, 214k of them reasoning).

Companion analysis: v1.4.29.
