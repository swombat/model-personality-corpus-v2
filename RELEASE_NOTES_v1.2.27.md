# v1.2.27 — Sonnet 5.5

2026-09-29. Adds 245 QA-checked raw samples: 125 freeflow (25 per condition)
and 120 values, `sonnet-5-5-or-pin-anthropic`, requested and returned model
`anthropic/claude-sonnet-5.5`. Anthropic pinned through OpenRouter, no fallbacks,
provider-default reasoning/sampling and unchanged frozen token ladders.
Release date 2026-09-28 is sourced to the official Claude announcement, retained
in `notes/sonnet-5-5-2026-09-28/`, not inferred from catalogue timestamps.

Corpus summary: 57,886 valid traces, 512 physical cells, 162 model identities.
Besides Sonnet, summary regeneration accounts for 1,080 values traces already
tracked before this release; no old collection was restarted or migrated.

Newly compiled harness runs now select the separately versioned BV1-Luna-v1
analysis arm; old compiled configurations remain legacy DeepSeek. Raw collection
and three-coder values methodology are unchanged. New paths prevent mixed arms.
29 harness tests passed. Full decision, limitations and analysis artifacts are in
the companion analysis release v1.4.18.

This is a cumulative repository archive. The previous actual GitHub/Zenodo release
was v1.2.16 (10.5281/zenodo.21802242); intervening prepared release-note files
are not evidence that those versions were separately archived. Existing tracked
changes since that release are included without rewriting their provenance.
