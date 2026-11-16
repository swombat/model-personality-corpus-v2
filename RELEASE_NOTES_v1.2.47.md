# v1.2.47 — Alibaba Qwen4 Max

2026-11-16. Adds 245 verified raw samples: 125 freeflow (25 per condition)
and 120 values, `qwen4-max-or-pin-alibaba`. Requested model: `qwen/qwen4-max`,
pinned to **Alibaba** through OpenRouter (endpoint `qwen/qwen4-max-20261115`),
no fallbacks, $1.50 / $4.50 per M. Reasoning and sampling are the provider's
defaults; prompts and technical retry budgets are unchanged. The model also
accepts images and video; this capture is text-only. Run
`20261116-qwen4-max-house`, collected on release day by Lume from the
souls.house container under the daily mapping rhythm.

Release date 2026-11-16 comes from Alibaba Cloud Model Studio's "Newly
released models" page, which lists `qwen4-max` on 2026-11-16 across its
international, global and mainland scopes (saved as `announcement.html`). The
same page lists `qwen4-max-preview` on 2026-11-11 as available through Token
Plan only; the general-availability date is used. Evidence is in
`notes/qwen4-max-2026-11-16/`. The OpenRouter listing timestamp is not used as
release evidence.

## Interventions

None. Every trace is the model's first valid answer under the normal ladders,
and no values sample needed adjudication (no initial or residual splits).

## Counts

The regenerated corpus summary reports 67,177 valid samples across 588 cells
and 194 distinct models (freeflow 35,751 / 326 cells; values 31,426 / 262
cells). These summary counts are not a claim that all historical samples
passed this run's QA.

Raw capture cost, counted once per trace with `scripts/capture_spend.py`:
$2.84 (627k completion tokens, 396k of them reasoning).

Accounting note: this capture ran on the OpenRouter key already present in the
souls.house container's environment, not on the research key whose usage the
runbook records (`run_capture.sh` uses an existing `OPENROUTER_API_KEY` before
its loader). The research key's usage moved only by the $0.14 banner render.
The per-trace figure above is the cost of record.

Companion analysis: v1.4.45.
