# v1.2.36 — Qwen3.8 Omni Flash

2026-10-16. Adds 245 verified raw samples: 125 freeflow (25 per condition)
and 120 values, `qwen3-8-omni-flash-or-pin-alibaba`. Requested model:
`qwen/qwen3.8-omni-flash`, pinned to Alibaba through OpenRouter, no fallbacks.
Reasoning and sampling are provider defaults; prompts, token ladders and
technical retry budgets are unchanged. Run `20261008-qwen3-8-omni-flash-house`,
collected 2026-10-08 by Lume from the souls.house container.

The capture was **held** from 8 to 16 October, unreleased. The raw data was
complete, but 8 of its 125 freeflow sources contain no sentence-ending
punctuation at all, and the BV1 evaluator's whole-sentence evidence rule could
not quote them. The hold note
(`notes/qwen3-8-omni-flash-2026-09-17/BV1-COVERAGE-HOLD.md`) records why and
now records the resolution: the analysis side adopted BV1-Luna v1.1, whose
excerpt rule applies only to such sources. No raw data changed. This release
moves the held branch (`hold/qwen3-8-omni-flash`, raw commit aab8d9011) into
master unaltered.

Release date 2026-09-17 comes from Alibaba Cloud Model Studio's "Newly released
models" page, saved with the endpoint snapshot in
`notes/qwen3-8-omni-flash-2026-09-17/`. The OpenRouter listing timestamp is not
used as release evidence.

## Interventions

None in raw collection: all 245 capture tasks completed within their normal
attempt budgets. The BV1 coverage hold and its resolution are on the analysis
side (companion release).

## Counts

The regenerated corpus summary reports 64,237 valid samples across 564 cells
and 182 distinct models (freeflow 34,251 / 314 cells; values 29,986 / 250
cells). These summary counts are not a claim that all historical samples
passed this run's QA.

Raw capture cost, summed from the per-call costs in the traces: $0.87
(1.85M completion tokens, 1.66M of them reasoning).

Companion analysis: v1.4.30.
