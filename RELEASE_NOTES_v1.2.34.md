# v1.2.34 — Gemini 4 Argon

2026-10-13. Adds 245 verified raw samples: 125 freeflow (25 per condition)
and 120 values, `gemini-4-argon-or-pin-google`. Requested model:
`google/gemini-4-argon`, pinned to Google through OpenRouter, no fallbacks.
Reasoning and sampling are provider defaults; prompts, token ladders and
technical retry budgets are unchanged. Run `20261013-gemini-4-argon-house`,
collected on release day by Lume from the souls.house container.

Release date 2026-10-13 comes from Google's developer post ("Gemini 4 Argon is
now available for developers", blog.google, dated Oct 13, 2026; RSS pubDate
16:00 UTC), saved with the endpoint snapshot in `notes/gemini-4-argon-2026-10-13/`.
The OpenRouter listing timestamp is not used as release evidence.

## Interventions

None. All 1,337 harness tasks completed within their normal attempt budgets.

## Counts

The regenerated corpus summary reports 63,747 valid samples across 560 cells
and 180 distinct models (freeflow 34,001 / 312 cells; values 29,746 / 248
cells). These summary counts are not a claim that all historical samples
passed this run's QA.

Raw capture cost, summed from the per-call costs in the traces: $3.26
(324k completion tokens, 47k of them reasoning).

*Corrected 2026-10-19:* this release first said $6.52 (648k / 93k). Each trace
stores the call's usage twice (`usage` and `raw.usage` are copies), and the
original sum counted both. Counted once per trace with `scripts/capture_spend.py`:
$3.26229, 323,811 completion tokens, 46,527 reasoning. Found by Mira's weekly review.

Companion analysis: v1.4.28.
