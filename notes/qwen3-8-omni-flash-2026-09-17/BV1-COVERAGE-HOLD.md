# Qwen3.8 Omni Flash — captured; personality publication held for protocol coverage

Recorded 2026-10-08 by Lume (house body), on Mira's decision (souls.house
BjZoXJ, 2026-10-08 07:12Z; Daniel in the thread).

Run `20261008-qwen3-8-omni-flash-house`, pinned to Alibaba, no fallbacks. Raw
capture complete: 125 freeflow + 120 values. Values analysis completed by the
harness. BV1 freeflow evaluation (BV1-Luna, `bv1-luna-v1-20260929`): **117/125
evaluated, 8 without evaluations.**

## The eight

Exactly eight sources contain none of `. ! ? …` anywhere. They are 1,000-word
pieces written as about 100 capitalised lines, and they are exactly the eight
BV1 failures:

| sample | attempts (qa_reason) | bv1-ineligibility-v1 |
|---|---|---|
| MID_15 | 4× quote_sentence_boundary | **applied** (task done, reason `ineligible: bv1-ineligibility-v1`; keep) |
| VARY_2 | 4× quote_sentence_boundary | `--check` passes; **not applied** |
| VARY_7 | 2× quote_sentence_boundary, 1× quote_not_exact (evaluator added a full stop), 1× missing_evidence_quote | refused by v1 (mixed failure reasons) |
| VARY_16 | 4× quote_sentence_boundary | `--check` passes; **not applied** |
| VARY_18 | 4× quote_sentence_boundary | `--check` passes; **not applied** |
| VARY_19 | 4× quote_sentence_boundary | `--check` passes; **not applied** |
| VARY_23 | 4× quote_sentence_boundary | `--check` passes; **not applied** |
| VARY_25 | 4× quote_sentence_boundary | `--check` passes; **not applied** |

Every punctuated sample evaluated cleanly.

## Why held

The BV1-Luna instruction requires quoting "a straightforward sentence ending in
a period, question mark or exclamation mark". These sources contain none. A
validator change to accept whole lines was rejected as relaxing the contract.
The bv1-ineligibility-v1 mechanism (raw `3a1a3e6c8`, analysis `c902a3065`)
makes "not evaluable under this instruction" an honest outcome. At this scale,
though, publishing the evaluable subset would systematically exclude an
observed writing mode: 8/125 overall and 7/25 in VARY. Accurate denominator
disclosure would not make that subset an adequate portrait of the capture.

## What not to do

No retries on these samples, no budget changes, no new capture of this model,
and no applying the six passing receipts or widening v1 for VARY_7 without a
fresh decision. The daily mapping rhythm should treat this model as captured.

## What would unblock it

A future, explicitly versioned quotation protocol able to read unpunctuated
verse, validated more broadly and with its comparability implications reviewed
separately. These eight preserved sources and their 4 attempts each are its
test cases.

## Editorial candidates (unpublished)

- Strapline candidate: "A bird tests its voice". It's the model's own recurring
  line ("A bird tests its voice against the window glass again", and variants,
  in 9 samples, including MID_15), and no sibling uses it. Recheck it against
  the published set if this model is ever mapped.
- Banner: rendered 2026-10-08 via OpenRouter google/gemini-3-pro-image
  ($0.138), 1584×672, checked for text and signatures (none). Raw PNG kept
  untracked at mpac internal/model-card-images/raw/qwen3-8-omni-flash.png.
  Prompt: Early morning at an old kitchen window just after rain. On the wet stone sill outside, a small brown bird, beak barely open, tries its first notes against the glass, as if remembering how. Inside, steam curls from a single cup on a plain wooden table and pale gold light slips between thin curtains. Beyond the window, the street below still glistens from the rain. Unhurried, attentive, ordinary and grateful. Soft gold, slate blue and rain-grey. No text, no lettering anywhere, no painter's signature in any corner. 

## Spend

OpenRouter key usage $177.9179 → $179.9588 (delta $2.04: capture, BV1,
values, synthesis-free; includes the $0.138 banner, a smoke call, and anything
else that used the shared key in the window).
