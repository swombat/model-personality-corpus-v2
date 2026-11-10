# v1.2.44 — Meta Muse Ember

2026-11-10. Adds 245 verified raw samples: 125 freeflow (25 per condition)
and 120 values, `muse-ember-or-pin-meta`. Requested model: `meta/muse-ember`,
pinned to **Meta** through OpenRouter (endpoint `meta/muse-ember-20261109`, the
only one), no fallbacks, $0.10 / $0.50 per M. Reasoning and sampling are the
provider's defaults; prompts and technical retry budgets are unchanged. Run
`20261110-muse-ember-house`, collected the day after release by Lume from the
souls.house container under the daily mapping rhythm.

Release date 2026-11-09 comes from Meta's own versioned endpoint id. Meta's
developer post (https://dev.meta.ai/resources/blog/build-with-muse-ember,
rendered page saved) is undated; Artificial Analysis also lists 2026-11-09.
Evidence in `notes/muse-ember-2026-11-09/`. The OpenRouter listing timestamp is
not used as release evidence.

Muse Ember is the released form of the stealth model Crouton Alpha
(`stealth/crouton-alpha`): on 2026-11-10 OpenRouter answered it with "This model
was an early version of Meta's Muse Ember" (saved in
`notes/crouton-alpha-2026-11-03/unmasked-2026-11-10.json`). Crouton was
region-blocked from our hosts and never captured; its built run was retired.

## Interventions

None to any raw sample: every trace is the model's first valid answer under the
normal ladders. Two analysis-side interventions are recorded in companion
v1.4.42: one BV1 evaluation (VARY_14) revalidated offline under the new
BV1-Luna v1.2 validator, with the harness lane `apply_bv1_offline.py` added in
this repo (30e8f4d6f), and one values split (G2_27) published under the
residual-disclosure policy. Both were reviewed and authorised by Mira.

## Counts

The regenerated corpus summary reports 66,197 valid samples across 580 cells
and 190 distinct models (freeflow 35,251 / 322 cells; values 30,946 / 258
cells). These summary counts are not a claim that all historical samples
passed this run's QA.

Raw capture cost, counted once per trace with `scripts/capture_spend.py`
(`upstream_inference_cost`): $0.42 (832k completion tokens, 605k of them
reasoning).

Companion analysis: v1.4.42.
