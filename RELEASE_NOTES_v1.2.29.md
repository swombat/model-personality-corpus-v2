# v1.2.29 — GPT-6.1 Sol

2026-09-29. Adds 245 verified raw samples: 125 freeflow (25 per condition)
and 120 values, `gpt-6-1-sol-or-pin-openai`. Requested/returned model:
`openai/gpt-6.1-sol`, pinned OpenAI through OpenRouter, no fallbacks.
This is standard Sol, not Pro or batch. Reasoning and sampling are provider
defaults; prompts, token ladders and retry bounds are unchanged.

Release date 2026-09-29 comes from the official OpenAI announcement, retrieved
through the model-mediated X reader with retained citations. The attempted
direct blog retrieval returned HTTP 403. Catalogue timestamps are not used
as release-date evidence. Endpoint and retrieval evidence are in
`notes/gpt-6-1-sol-2026-09-29/`.

Companion analysis v1.4.20 uses the separately versioned BV1-Luna arm and
unchanged three-coder values pipeline. One analysis reading was recovered
from retained output after a documented quotation-boundary validator correction;
no raw sample was altered and no inference allowance increased.

The regenerated corpus summary reports 62,186 nonempty samples, 547 physical
cells and 175 normalized model identities. These summary counts are not a
claim that all historical samples passed this run's stricter QA.
