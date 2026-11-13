# v1.2.46 — Gemini 4 Hydrogen and Inkling 2 Small

2026-11-13. Adds 490 raw samples: 125 freeflow and 120 values per model.
Companion analysis: v1.4.44.

- `google/gemini-4-hydrogen`, cell `gemini-4-hydrogen-or-pin-google`, pinned to
  Google through OpenRouter, no fallbacks, provider-default reasoning and
  sampling. Google released it on 2026-11-12 (saved announcement's
  datePublished 18:00Z), at flat $1.50/$7.50 per million. Evidence:
  `notes/gemini-4-hydrogen-2026-11-12/`.
- `thinkingmachines/inkling-2-small`, cell `inkling-2-small-or-pin-together`,
  pinned to Together through OpenRouter, no fallbacks, provider-default
  reasoning and sampling. This is explicitly a **third-party-hosted** reading:
  OpenRouter had no Thinking Machines route. Daniel approved using a sensible
  third-party host in souls.house YZxogj/jVvPMa; the lab's post names Together.
  Release date 2026-11-05, with open weights from 2026-11-12. Evidence:
  `notes/inkling-2-small-2026-11-05/`.

Lume ran capture and analysis under the daily mapping rhythm. Both recovered
task status receipts report all 1,337 tasks done, with no blockers (Hydrogen
06:13 CET; Inkling 10:27 CET). Mira recovered only the research artifacts and
finished publication after the Claude incident interrupted Lume's work.
No sample intervention or budget change is recorded for either run; prompts,
methodology and technical retry ladders are unchanged.

The regenerated summary counts 66,932 valid samples across 586 cells and 193
distinct models: freeflow 35,626 / 325 cells; values 31,306 / 261 cells.
These historical corpus totals are not a claim that every historical sample
passed the current QA.

Capture spend, counted once per trace with `scripts/capture_spend.py`:

| Model | Traces | Cost | Completion tokens | Reasoning tokens |
|---|---:|---:|---:|---:|
| Hydrogen | 245 | $6.26599 | 833,040 | 588,184 |
| Inkling 2 Small | 245 | $0.29678 | 294,682 | 94,178 |

All 490 traces contain usage. These are raw capture costs, not total analysis
costs; the original shared key's full usage delta was not recovered.
