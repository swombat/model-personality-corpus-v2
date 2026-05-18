# Release notes — v1.2.1

Prepared: 2026-05-18

## Corpus changes

- Completes the N=125 freeflow top-up plan after final retry/fill work.
- Expanded the release corpus to **31,456 valid samples** across **296 cells** and **57 distinct models**.
- Freeflow: **17,670 valid samples** across **181 cells**.
- Values: **13,786 valid samples** across **115 cells** (unchanged from v1.2.0).
- Verified all labels in `N125_TOPUP_COLLECTION_PLAN.md` are complete at **125/125 valid freeflow samples**.
- Filled the final near-complete OpenAI direct cells (`gpt-5.5-pro`, `gpt-5-codex`, `gpt-5.1`, `gpt-5.1-codex`) and the delayed direct Gemini 2.5 Pro cell.

## QA

- Regenerated `data/CORPUS_SUMMARY.md`.
- Regenerated `data/n75_composite_summary.tsv`.
- Final top-up QA script found no incomplete planned N=125 labels.

## Release status

- Prepared for commit, tag, push, and Zenodo pickup as `v1.2.1`.
