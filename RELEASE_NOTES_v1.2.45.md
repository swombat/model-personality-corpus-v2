# v1.2.45 — Google Gemini 4 Carbon

2026-11-11. Adds 245 verified raw samples: 125 freeflow (25 per condition)
and 120 values, `gemini-4-carbon-or-pin-google`. Requested model:
`google/gemini-4-carbon`, pinned to **Google** through OpenRouter (endpoint
`google/gemini-4-carbon-20261110`), no fallbacks, Google's introductory price of
$2 / $10 per M. Reasoning and sampling are the provider's defaults; prompts and
technical retry budgets are unchanged. Run `20261111-gemini-4-carbon-house`,
collected the day after release by Lume from the souls.house container under
the daily mapping rhythm.

Release date 2026-11-10 comes from Google's own posts, "Gemini 4 Carbon is now
available" and "Gemini 4 Carbon is now available for developers" (blog.google,
schema.org datePublished 2026-11-10T16:00Z; both saved). Evidence is in
`notes/gemini-4-carbon-2026-11-10/`. The OpenRouter listing timestamp is not
used as release evidence. Google describes Carbon as a distinct model from
Gemini 4 Argon, "built for tasks that test the limits of a model's
intelligence … using more tokens than Argon", so it was mapped as a new model
and not skipped as a reasoning-mode SKU.

The price is introductory. Footnote 1 of Google's models post: after the
introductory period expires on November 30, 2026, $4 per 1M input tokens and
$20 per 1M output tokens apply. (Found by Mira's evidence helper; confirmed in
the saved copy.)

## Interventions

None to any raw sample: every trace is the model's first valid answer under the
normal ladders. One analysis-side intervention is recorded in companion
v1.4.43: two values splits (G2_2, G2_12) are published under the
residual-disclosure policy, reviewed and authorised by Mira for this capture
only.

## Counts

The regenerated corpus summary reports 66,442 valid samples across 582 cells
and 191 distinct models (freeflow 35,376 / 323 cells; values 31,066 / 259
cells). These summary counts are not a claim that all historical samples
passed this run's QA.

Raw capture cost, counted once per trace with `scripts/capture_spend.py`
(`upstream_inference_cost`): $5.29 (527k completion tokens, 250k of them
reasoning). Gemini 4 Argon's capture, for comparison: $3.26 (324k / 47k).

Companion analysis: v1.4.43.
