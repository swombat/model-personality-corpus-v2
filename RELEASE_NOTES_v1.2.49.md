# v1.2.49 — Google Gemini 4 Neon

2026-11-19. Adds 245 verified raw samples: 125 freeflow (25 per condition) and
120 values. Cell: `gemini-4-neon-or-pin-google`. Requested model:
`google/gemini-4-neon` ($3 / $15 per M), pinned to **Google** (Vertex global,
standard tier) through OpenRouter, with no fallbacks and no service tier
requested (not flex, not priority). Reasoning and sampling are the provider's
defaults (high thinking level). Prompts and technical retry budgets are
unchanged. Run `20261119-gemini-4-neon-house` was collected the day after
release by Lume from the souls.house container, under the daily-mapping
remit (Daniel, souls.house BjZoXJ).

The release date, 2026-11-18, comes from Google's post "Introducing Gemini 4
Neon" (schema.org datePublished 2026-11-18T21:00:00Z), saved as
`announcement.html` in `notes/gemini-4-neon-2026-11-18/`. The OpenRouter
listing timestamp is not used as release evidence.

## Interventions

None to any raw sample. Every trace is the model's first valid answer under
the normal ladders. Values splits were settled by the standard single
independent adjudication; one residual split (`G2_5`) is published with
disclosure in the companion analysis under a per-capture policy approved by
Mira (souls.house jXkgVe). That affects analysis, not the raw traces here.

## Counts

The regenerated corpus summary reports 67,912 valid samples across 594 cells
and 197 distinct models (freeflow 36,126 / 329 cells; values 31,786 / 265
cells). These summary counts are not a claim that all historical samples
passed this run's QA.

Raw capture cost, counted once per trace (`scripts/capture_spend.py`):
$12.17 (809k completion tokens, 576k reasoning).

Companion analysis: v1.4.48.
