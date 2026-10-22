# v1.2.39: MiniMax M3.1 Flash and Inception Mercury 3

2026-10-22. Adds 490 verified raw samples in two cells, each with 125 freeflow samples (25 per condition) and 120 values samples. Both were collected three days after release by Lume from the souls.house container. Reasoning and sampling are the provider's defaults, there are no fallbacks, and prompts are unchanged.

| Cell | Requested model | Pin | Run | Released |
|---|---|---|---|---|
| `minimax-m3-1-flash-or-pin-minimax` | `minimax/minimax-m3.1-flash` | Minimax | `20261022-minimax-m3-1-flash-house` | 2026-10-19 |
| `mercury-3-or-pin-inception` | `inception/mercury-3` | Inception | `20261022-mercury-3-house` | 2026-10-19 |

Release dates come from the labs' own posts: MiniMax's announcement (https://www.minimax.io/blog/minimax-m31f, schema.org datePublished) and Inception's blog post (https://www.inceptionlabs.ai/blog/introducing-mercury-3). Both are saved with their endpoint snapshots in `notes/minimax-m3-1-flash-2026-10-19/` and `notes/mercury-3-2026-10-19/`. OpenRouter listing timestamps are not used as release evidence.

Mercury 3 is Inception's diffusion language model and the successor to Mercury 2.5. It was captured at the launch price ($0.10/$0.35 per M, 50% off list). MiniMax states that the anonymous OpenRouter model Space Bunny (captured 2026-09-23, v1.2.28 cell `space-bunny-alpha-or-pin-stealth`) "was an early version of MiniMax M3.1 Flash".

Both models were caught late. The daily detection run missed them, and Daniel flagged them. The detector now follows every lab already in the corpus.

## Interventions

**MiniMax M3.1 Flash: six LONG freeflow samples replaced (authorised).** Under the standard freeflow policy (a 16,000-token attempt, then 32,768), 6 of the 25 LONG prompts (24%; 6/125 freeflow overall) returned empty content with `finish_reason=length`. The six were LONG_1, LONG_6, LONG_9, LONG_12, LONG_18 and LONG_19. Each exhausted the 32,768 ceiling in hidden reasoning, which was mostly paragraph-by-paragraph word counting toward the requested 2,500 words.

Daniel authorised a bounded repair (souls.house oewwDe, eGaNNJ) after Mira's review (eZKlbY, YlxzVY). Each sample was re-requested at 65,536 under the same prompt, pin and defaults; a 131,072 step was authorised but not needed. All six succeeded on that one request, using 9,804, 5,820, 4,232, 47,082, 24,538 and 27,348 completion tokens. The published traces for these six are therefore replacements selected after empty-output failures, not standard-policy draws. They were fresh draws at a changed ceiling, and which of the two mattered is not isolated.

The failed originals are preserved:
- in `discarded/20261022-minimax-m3-1-flash-house-long-repair/` (copies; their SHA256s are in the receipts);
- in the analysis repo's `raw_attempts/` for the phase.

The repair script and its per-sample receipts are in `notes/minimax-m3-1-flash-2026-10-19/long-repair/`. The run spec and harness code were not changed. Do not read this cell as a single fixed-budget capture.

Mercury 3: no capture interventions. All 1,337 harness tasks completed within normal budgets. The values publication policy for its one residual split is an analysis-side matter; see analysis v1.4.34.

## Counts

The regenerated corpus summary reports 64,972 valid samples across 570 cells and 185 distinct models (freeflow 34,626 / 317 cells; values 30,346 / 253 cells). These summary counts are not a claim that all historical samples passed this run's QA.

Raw capture cost, summed from the per-call costs in the published traces:
- MiniMax M3.1 Flash: $0.64 (1.05M completion tokens, 0.86M of them reasoning).
- Mercury 3: $0.13 (379k completion tokens, 179k reasoning).

Failed draws are not included. The OpenRouter key's usage moved $2.76 over the whole session, including both captures, analysis, repairs and two banner renders.

Companion analysis: v1.4.34.
