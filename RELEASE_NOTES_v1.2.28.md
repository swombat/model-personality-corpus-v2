# v1.2.28 — raw captures for models already published

2026-09-29. Adds 4,055 raw samples in 33 cells: 19 freeflow cells (125 each) and
14 values cells (120 each). No new collection was run for this release. These
captures were made between 13 August and 23 September 2026, analysed, and
published on the companion site, but the raw traces had stayed uncommitted on
the collection machine. v1.2.27's corpus summary therefore listed seven published
models as "freeflow not collected". They were collected; they were not in the
repository.

## Cells added

Freeflow and values:

- Claude Opus 5.5 (`claude-opus-5-5-or-pin-anthropic`)
- GPT-6 Luna, GPT-6 Sol (`…-or-pin-openai`)
- Gemini 3.8 Flash (`gemini-3-8-flash-or-pin-google`)
- Muse Spark 1.1, 1.2, 1.3 and the two contributor cells; Muse Glimmer 30B
- Qwen2.5-7B-Instruct (local Transformers/MPS cell, revision a09a3545)
- Space Bunny Alpha (`space-bunny-alpha-or-pin-stealth`), an anonymous
  OpenRouter route; lab unknown

Freeflow only (values were already tracked):

- Grok 4.7, GLM-5.3-FlashX, Qwen3.8-27B
- MiMo-V2.5, MiMo-V2.6-Flash, MiMo-V2.6-Pro, MiMo-V2.6-Pro-UltraSpeed

Values only:

- Qwen3.8-27B and Ternary Bonsai 2 27B, medium-reasoning condition. Their coded
  values rows are in the analysis release; their freeflow cells are not
  committed here because the freeflow analysis is unfinished.

Six collection manifests for the runs above are added.

## Checks

Every added file parses, has a non-empty `result`, and `finish_reason: stop`.
Files were searched for the collection keys themselves and for standalone
key-shaped tokens and authorisation headers; none found. Traces are committed
as captured.

Corpus summary, regenerated from a clean checkout of this release: 61,941 valid
samples, 545 physical cells, 174 model identities (v1.2.27: 57,886 / 512 / 162).

## Not included

Collected but left uncommitted, for their collector to release: MiMo-V2.5-Pro
freeflow; Qwen3.8-27B and Ternary Bonsai 2 27B medium-reasoning freeflow;
Ternary Bonsai 2 27B freeflow (14 of its 25 LONG samples ended at the token
cap and 13 have no result); a local DeepSeek-LLM-7B cell with 31 empty results;
the repaired GLM-5.3 LONG traces; and four `discarded/` attempt directories.

The note in the Space Bunny Alpha manifest, "No publication authorized", dates
from the capture on 2026-09-23. Publication was authorised by Daniel Tenner on
2026-09-29.

Companion analysis release: v1.4.19.
