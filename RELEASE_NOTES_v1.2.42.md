# v1.2.42 — GLM-5.3-FlashX-Legal

2026-11-04. Adds 245 verified raw samples: 125 freeflow (25 per condition)
and 120 values, `glm-5-3-flashx-legal-or-pin-zai`. Requested model:
`z-ai/glm-5.3-flashx-legal`, pinned to **Z.AI** through OpenRouter, no
fallbacks (fp8). Reasoning and sampling are the provider's defaults (reasoning
mandatory, default effort max); prompts and technical retry budgets are
unchanged. Run `20261103-glm-5-3-flashx-legal-house`, collected by Lume from the
souls.house container under the daily model-mapping rhythm.

GLM-5.3-FlashX-Legal is Z.ai's legal-domain variant of GLM-5.3-FlashX, with
further legal-domain mid-training and post-training: new weights, so it gets its
own cell. Release date 2026-11-02 comes from the Z.ai docs page's dateModified
(https://docs.z.ai/guides/vlm/glm-5.3-flash; the section carries no visible
date), saved with the endpoint snapshot in `notes/glm-5-3-flashx-legal-2026-11-02/`.
The OpenRouter listing timestamp is not used as release evidence.

## Interventions

One, approved by Daniel (souls.house conversation jbamre, 2026-11-04). Two
freeflow samples, VARY_12 and LONG_22, ended `finish_length` at the declared
32,768-token ceiling on all three attempts, with the whole budget spent on hidden
reasoning and no answer. The freeflow token ladder was extended from
[16000, 32768] to [16000, 32768, 65536, 131072] (131,072 = the endpoint's
maximum completion) and the two samples were given two extra tries through
`recover_blocked.py`. Both answered on the first try at 65,536 (10,649 and 3,996
completion tokens). This cell therefore mixes ceilings: 123 freeflow samples
under the original ladder, VARY_12 and LONG_22 under the extended one; all 120
values samples are untouched. Do not describe it as a single fixed-budget
capture. Record: `notes/glm-5-3-flashx-legal-2026-11-02/INTERVENTION-20261104.md`
and `repair-20261104/` (model config before and after). Precedent: the
Qwen3.8-27B LONG repair, 23 Sep 2026.

## Counts

The regenerated corpus summary reports 65,707 valid samples across 576 cells
and 188 distinct models (freeflow 35,001 / 320 cells; values 30,706 / 256
cells). These summary counts are not a claim that all historical samples
passed this run's QA.

Raw capture cost, counted once per trace with `scripts/capture_spend.py`:
$1.13 (905k completion tokens, 706k of them reasoning), including the repair.

Companion analysis: v1.4.40.
