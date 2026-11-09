# v1.2.43 — Claude Fable 5.2

2026-11-10. Adds 245 verified raw samples: 125 freeflow (25 per condition)
and 120 values, `fable-5-2-or-pin-anthropic`. Requested model:
`anthropic/claude-fable-5.2`, pinned to **Anthropic** through OpenRouter, no
fallbacks, standard tier ($8 / $40 per M; the 2x `anthropic/fast` priority
endpoint was not used). Reasoning and sampling are the provider's defaults;
prompts and technical retry budgets are unchanged. Run
`20261109-fable-5-2-house`, collected on release day by Lume from the
souls.house container, at Daniel's request.

Release date 2026-11-09 comes from Anthropic's announcement page
(https://www.anthropic.com/claude-fable-and-mythos-5-2, "November 9, 2026"),
saved with the endpoint snapshot in `notes/fable-5-2-2026-11-09/`. The
OpenRouter listing timestamp is not used as release evidence.

## Interventions

None to any sample. The harness process stopped at 23:33 (9 Nov) with 733 of
1,337 tasks done, none blocked or failed; it was restarted unchanged at 00:20
and resumed from its state database. No budget, ladder or spec was changed.

## Counts

The regenerated corpus summary reports 65,952 valid samples across 578 cells
and 189 distinct models (freeflow 35,126 / 321 cells; values 30,826 / 257
cells). These summary counts are not a claim that all historical samples
passed this run's QA.

Raw capture cost, counted once per trace with `scripts/capture_spend.py`
(`upstream_inference_cost`; BYOK, billed to the Anthropic key): $27.96 (698k
completion tokens, 435k of them reasoning).

Companion analysis: v1.4.41.
